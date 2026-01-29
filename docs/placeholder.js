/* placeholder.js —— 直接替换 */
(() => {
  'use strict';
  const ASSET_BASE = new URL('.', location.href).toString();
  window.__ASSET_BASE__ = window.__ASSET_BASE__ || ASSET_BASE;

  // ---------- 仅对 Render /health 做 no-cors 猴补 ----------
  (function patchFetchForRenderHealth() {
    const orig = window.fetch;
    window.fetch = async function(input, init = {}) {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      const method = (init.method || 'GET').toUpperCase();
      if (/^https?:\/\/[^/]*onrender\.com\/health(?:\?|$)/i.test(url) && method === 'GET') {
        const patched = { ...init, mode: 'no-cors' };
        const res = await orig(url, patched);
        if (res.type === 'opaque') return new Response('', { status: 200, statusText: 'OK' });
        return res;
      }
      return orig(input, init);
    };
  })();

  // ---------- 基础工具 ----------
  const HEALTH_TTL = 60_000;
  const HEALTH_CACHE = new Map(); // base => { ok, ts }

  const isWorkerLike = (host) => /workers\.dev|^worker\.|proxy|cloudflare/i.test(host);
  const isRender = (host) => /(^|\.)onrender\.com$/i.test(host);

  function normalizeBase(base) {
    if (!base) return null;
    try {
      const u = new URL(base, location.href);
      const p = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
      return `${u.origin}${p}`;
    } catch { return null; }
  }

  function join(base, path) {
    const b = (base || '').replace(/\/+$/, '');
    const p = (String(path) || '').replace(/^\/+/, '');
    return b && p ? `${b}/${p}` : b || p || '';
  }

  // Render 仅 /health；其余优先 /api/health
  function healthPathsFor(base) {
    try {
      const u = new URL(base, location.href);
      if (isRender(u.hostname)) return ['/health'];
    } catch {}
    return ['/api/health', '/health'];
  }

  // 解析 & 排序（Worker 优先）
  function resolveApiBases(input) {
    const raw = Array.isArray(input) ? input.join(',') : (input || '');
    const seen = new Set(), list = [];
    raw.split(',').map(s => s.trim()).filter(Boolean).forEach(b => {
      const n = normalizeBase(b);
      if (n && !seen.has(n)) { seen.add(n); list.push(n); }
    });
    return list.sort((a, b) => {
      const ha = new URL(a, location.href).hostname;
      const hb = new URL(b, location.href).hostname;
      const sa = isWorkerLike(ha) ? 0 : isRender(ha) ? 2 : 1;
      const sb = isWorkerLike(hb) ? 0 : isRender(hb) ? 2 : 1;
      return sa - sb; // Worker(0) < Other(1) < Render(2)
    });
  }

  async function isHealthy(base, timeoutMs = 2500) {
    const b = normalizeBase(base);
    if (!b) return false;
    for (const p of healthPathsFor(b)) {
      const url = join(b, p);
      try {
        const c = new AbortController();
        const t = setTimeout(() => c.abort('timeout'), timeoutMs);
        const res = await fetch(url, { method: 'GET', mode: 'cors', cache: 'no-store', credentials: 'omit', signal: c.signal });
        clearTimeout(t);
        if (res.ok || res.status === 200) return true;
      } catch {}
    }
    return false;
  }

  async function warmUp(apiBases, { timeoutMs = 2500, useCache = true } = {}) {
    const bases = resolveApiBases(apiBases);
    if (!bases.length) return { healthy: [], unhealthy: [] };
    const now = Date.now();
    const tasks = bases.map(async (b) => {
      const c = HEALTH_CACHE.get(b);
      if (useCache && c && now - c.ts < HEALTH_TTL) return { base: b, ok: c.ok, source: 'cache' };
      const ok = await isHealthy(b, timeoutMs);
      HEALTH_CACHE.set(b, { ok, ts: Date.now() });
      return { base: b, ok, source: 'probe' };
    });
    const r = await Promise.all(tasks);
    return { healthy: r.filter(x => x.ok).map(x => x.base), unhealthy: r.filter(x => !x.ok).map(x => x.base) };
  }

  async function pickHealthyBase(apiBases, opts = {}) {
    const bases = resolveApiBases(apiBases);
    if (!bases.length) return null;

    // 先看缓存（且保持排序优先级）
    for (const b of bases) {
      const c = HEALTH_CACHE.get(b);
      if (c && c.ok && (Date.now() - c.ts) < HEALTH_TTL) return b;
    }

    const { healthy } = await warmUp(bases, opts);
    // 维持排序优先级
    for (const b of bases) if (healthy.includes(b)) return b;
    return null;
  }

  async function postJsonWithRetry(apiBases, path, payload, retry = 1, rawPayload) {
    const bases = resolveApiBases(apiBases);
    if (!bases.length) throw new Error('未配置后端 API 地址');

    const body = typeof rawPayload === 'string' ? rawPayload : JSON.stringify(payload);
    if (/data:[^;]+;base64,/.test(body) || body.length > 300000) {
      throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
    }

    let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    if (!base) { base = bases[0]; void warmUp(bases).catch(() => {}); }

    let lastErr = null;
    for (let attempt = 0; attempt <= retry; attempt++) {
      const order = base ? [base, ...bases.filter(x => x !== base)] : [...bases];
      for (const b of order) {
        try {
          const res = await fetch(join(b, path), {
            method: 'POST',
            mode: 'cors',
            cache: 'no-store',
            credentials: 'omit',
            headers: { 'Content-Type': 'application/json' },
            body,
          });
          if (!res.ok) {
            const txt = await res.text().catch(() => '');
            throw new Error(txt || `HTTP ${res.status}`);
          }
          HEALTH_CACHE.set(b, { ok: true, ts: Date.now() });
          return res;
        } catch (e) {
          lastErr = e;
          HEALTH_CACHE.set(b, { ok: false, ts: Date.now() });
          base = null; // 下一轮重选
        }
      }
      try { await warmUp(bases, { timeoutMs: 2500 }); } catch {}
      await new Promise(r => setTimeout(r, 800));
      base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    }
    throw lastErr || new Error('请求失败');
  }

  // ---------- 导出 ----------
  const ns = (window.MPoster = window.MPoster || {});
  Object.assign(ns, { resolveApiBases, warmUp, pickHealthyBase, postJsonWithRetry, isHealthy });

  window.resolveApiBases   = window.resolveApiBases   || ns.resolveApiBases;
  window.warmUp            = window.warmUp            || ns.warmUp;
  window.pickHealthyBase   = window.pickHealthyBase   || ns.pickHealthyBase;
  window.postJsonWithRetry = window.postJsonWithRetry || ns.postJsonWithRetry;
  window.isHealthy         = window.isHealthy         || ns.isHealthy;
})();
