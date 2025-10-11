/* placeholder.js — 只暴露全局工具 + Render/health CORS 兜底 */
(() => {
  'use strict';

  // ------------------------------------------------------------
  // 1) 针对 Render /health 的 CORS 猴补：强制 no-cors，并把结果视为 ok
  // ------------------------------------------------------------
  (function patchFetchForRenderHealth() {
    const origFetch = window.fetch;
    window.fetch = async function(input, init = {}) {
      try {
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        const method = (init.method || 'GET').toUpperCase();

        // 仅拦 Render 的 /health GET
        if (
          /^https?:\/\/[^/]*onrender\.com\/health(?:\?|$)/i.test(url) &&
          method === 'GET'
        ) {
          const patchedInit = { ...init, mode: 'no-cors' };
          const res = await origFetch(url, patchedInit);

          // no-cors 的响应是 opaque，.ok === false，为了探活直接视为 ok
          if (res.type === 'opaque') {
            return new Response('', { status: 200, statusText: 'OK' });
          }
          return res;
        }

        return await origFetch(input, init);
      } catch (e) {
        return Promise.reject(e);
      }
    };
  })();

  // ------------------------------------------------------------
  // 2) 基础工具 & 健康检查/选择/重试
  // ------------------------------------------------------------
  const HEALTH_TTL_MS = 60_000;          // 60s 探活缓存
  const HEALTH_CACHE = new Map();        // base -> { ok, ts }

  function normalizeBase(base) {
    if (!base) return null;
    try {
      const u = new URL(base, window.location.href);
      const pathname = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
      return `${u.origin}${pathname}`;
    } catch {
      return null;
    }
  }

  function joinBasePath(base, path) {
    const b = (base || '').replace(/\/+$/, '');
    const p = (path || '').replace(/^\/+/, '');
    return b && p ? `${b}/${p}` : b || p || '';
  }

  // Render 只允许 /health；其他域名优先试 /api/health
  function healthPathsFor(base) {
    try {
      const u = new URL(base, location.href);
      if (/onrender\.com$/i.test(u.hostname)) return ['/health'];
    } catch {}
    return ['/api/health', '/health'];
  }

  // 兼容数组/逗号分隔/单字符串
  function resolveApiBases(input) {
    const raw = Array.isArray(input) ? input.join(',') : (input || '');
    const seen = new Set();
    const out = [];
    raw.split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .forEach(b => {
        const n = normalizeBase(b);
        if (n && !seen.has(n)) { seen.add(n); out.push(n); }
      });
    return out;
  }

  async function isHealthy(base, timeoutMs = 2500) {
    const b = normalizeBase(base);
    if (!b) return false;

    for (const p of healthPathsFor(b)) {
      const url = joinBasePath(b, p);
      try {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort('timeout'), timeoutMs);
        const res = await fetch(url, {
          method: 'GET',
          mode: 'cors',         // 对 Render 会被猴补为 no-cors
          cache: 'no-store',
          credentials: 'omit',
          signal: ctrl.signal,
        });
        clearTimeout(timer);
        if (res.ok) return true;     // 普通 CORS 情况
        // 如果被猴补为 no-cors，我们在 fetch 补丁里已经返回了 {status:200}
        if (res.status === 200) return true;
      } catch {
        // 忽略，换下一个 path
      }
    }
    return false;
  }

  async function warmUp(apiBaseOrBases, { timeoutMs = 2500, useCache = true } = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return { healthy: [], unhealthy: [] };

    const now = Date.now();
    const tasks = bases.map(async (b) => {
      const cached = HEALTH_CACHE.get(b);
      if (useCache && cached && now - cached.ts < HEALTH_TTL_MS) {
        return { base: b, ok: cached.ok, source: 'cache' };
      }
      const ok = await isHealthy(b, timeoutMs);
      HEALTH_CACHE.set(b, { ok, ts: Date.now() });
      return { base: b, ok, source: 'probe' };
    });

    const results = await Promise.all(tasks);
    return {
      healthy: results.filter(r => r.ok).map(r => r.base),
      unhealthy: results.filter(r => !r.ok).map(r => r.base),
    };
  }

  async function pickHealthyBase(apiBaseOrBases, opts = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return null;

    // 先看缓存
    const cached = bases.find(b => {
      const c = HEALTH_CACHE.get(b);
      return c && c.ok && (Date.now() - c.ts) < HEALTH_TTL_MS;
    });
    if (cached) return cached;

    const { healthy } = await warmUp(bases, opts);
    return healthy[0] || null;
  }

  async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) throw new Error('未配置后端 API 地址');

    const bodyRaw = typeof rawPayload === 'string' ? rawPayload : JSON.stringify(payload);
    if (/data:[^;]+;base64,/.test(bodyRaw) || bodyRaw.length > 300000) {
      throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
    }

    let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    if (!base) {
      base = bases[0];
      void warmUp(bases).catch(() => {});
    }

    const urlFor = (b) => joinBasePath(b, String(path));

    let lastErr = null;
    for (let attempt = 0; attempt <= retry; attempt += 1) {
      const order = base ? [base, ...bases.filter(x => x !== base)] : bases;
      for (const b of order) {
        try {
          const res = await fetch(urlFor(b), {
            method: 'POST',
            mode: 'cors',                // 业务接口必须 CORS
            cache: 'no-store',
            credentials: 'omit',
            headers: { 'Content-Type': 'application/json' },
            body: bodyRaw,
          });
          if (!res.ok) {
            const text = await res.text().catch(() => '');
            throw new Error(text || `HTTP ${res.status}`);
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

  // ------------------------------------------------------------
  // 3) 导出到全局（给 app.js 用）
  //    —— 一定要保证 placeholder.js 在 app.js 之前加载
  // ------------------------------------------------------------
  window.resolveApiBases  = window.resolveApiBases  || resolveApiBases;
  window.warmUp           = window.warmUp           || warmUp;
  window.pickHealthyBase  = window.pickHealthyBase  || pickHealthyBase;
  window.postJsonWithRetry= window.postJsonWithRetry|| postJsonWithRetry;
  window.isHealthy        = window.isHealthy        || isHealthy;

  // 同时挂一个命名空间，便于以后引用
  window.MPoster = {
    resolveApiBases, warmUp, pickHealthyBase, postJsonWithRetry, isHealthy
  };
})();
