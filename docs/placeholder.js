/* placeholder.js — worker/render 探活 + 选择 + 重试
 * 仅暴露 window.MPoster，避免与 app.js 顶层符号冲突
 */
(() => {
  'use strict';

  // ---------- 常量与缓存 ----------
function healthPathsFor(base) {
  try {
    const u = new URL(base, location.href);
    // Render 只允许 /health
    if (/onrender\.com$/.test(u.hostname)) return ['/health'];
  } catch {}
  // Worker 或自建网关优先 /api/health
  return ['/api/health', '/health'];
}

// 探活里用上：
async function isHealthy(base) {
  const baseNoSlash = base.replace(/\/$/, '');
  for (const p of healthPathsFor(base)) {
    try {
      const r = await fetch(`${baseNoSlash}${p}`, { method: 'GET', mode: 'cors', cache: 'no-store', credentials: 'omit' });
      if (r.ok) return true;
    } catch {}
  }
  return false;
}
  const HEALTH_TTL_MS = 60_000; // 探活结果缓存 60s
  const _healthCache = new Map(); // key=base, val={ ok, ts }

  // ---------- 工具 ----------
  function normalizeBase(base) {
    if (!base) return null;
    try {
      const u = new URL(base, window.location.href);
      // 去掉末尾多余的斜杠
      const pathname = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
      return `${u.origin}${pathname}`;
    } catch {
      return null;
    }
  }

  function resolveApiBases(input) {
    // 支持数组、逗号分隔字符串、单个字符串
    const raw = Array.isArray(input) ? input.join(',') : (input || '');
    const seen = new Set();
    const out = [];
    raw.split(',')
       .map(s => s.trim())
       .filter(Boolean)
       .forEach((b) => {
         const n = normalizeBase(b);
         if (n && !seen.has(n)) { seen.add(n); out.push(n); }
       });
    return out;
  }

  function fetchWithTimeout(url, init = {}, timeoutMs = 2500) {
    const c = new AbortController();
    const t = setTimeout(() => c.abort('timeout'), timeoutMs);
    return fetch(url, { ...init, signal: c.signal }).finally(() => clearTimeout(t));
  }

  async function isHealthy(base, timeoutMs = 2500) {
    const b = normalizeBase(base);
    if (!b) return false;
    for (const p of HEALTH_PATHS) {
      try {
        const res = await fetchWithTimeout(`${b}${p}`, {
          method: 'GET',
          mode: 'cors',
          cache: 'no-store',
          credentials: 'omit',
        }, timeoutMs);
        if (res.ok) return true;
      } catch { /* ignore and try next */ }
    }
    return false;
  }

  // ---------- 并发探活 ----------
  async function warmUp(apiBaseOrBases, { timeoutMs = 2500, useCache = true } = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return { healthy: [], unhealthy: [] };
    const now = Date.now();

    const tasks = bases.map(async (b) => {
      const cached = _healthCache.get(b);
      if (useCache && cached && now - cached.ts < HEALTH_TTL_MS) {
        return { base: b, ok: cached.ok, source: 'cache' };
      }
      const ok = await isHealthy(b, timeoutMs);
      _healthCache.set(b, { ok, ts: Date.now() });
      return { base: b, ok, source: 'probe' };
    });

    const results = await Promise.all(tasks);
    return {
      healthy: results.filter(r => r.ok).map(r => r.base),
      unhealthy: results.filter(r => !r.ok).map(r => r.base),
    };
  }

  // ---------- 选择健康基址（含缓存命中） ----------
  async function pickHealthyBase(apiBaseOrBases, opts = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return null;

    // 先用缓存
    const cached = bases.find(b => {
      const c = _healthCache.get(b);
      return c && c.ok && (Date.now() - c.ts) < HEALTH_TTL_MS;
    });
    if (cached) return cached;

    const { healthy } = await warmUp(bases, opts);
    return healthy[0] || null;
  }

  // ---------- POST JSON（带自动回退与重试） ----------
  async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) throw new Error('未配置后端 API 地址');

    const bodyRaw = JSON.stringify(payload);
    // 防止把大体积或 dataURL 直接塞进请求
    if (/data:[^;]+;base64,/.test(bodyRaw) || bodyRaw.length > 300000) {
      throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
    }

    const mkUrl = (b) => `${b.replace(/\/$/, '')}/${String(path).replace(/^\/+/, '')}`;

    let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    let lastErr = null;

    for (let attempt = 0; attempt <= retry; attempt += 1) {
      const order = base ? [base, ...bases.filter(x => x !== base)] : bases;
      for (const b of order) {
        try {
          const res = await fetch(mkUrl(b), {
            method: 'POST',
            mode: 'cors',
            cache: 'no-store',
            credentials: 'omit',
            headers: { 'Content-Type': 'application/json' },
            body: bodyRaw,
          });
          if (!res.ok) {
            const text = await res.text().catch(() => '');
            throw new Error(text || `HTTP ${res.status}`);
          }
          _healthCache.set(b, { ok: true, ts: Date.now() });
          return res;
        } catch (e) {
          lastErr = e;
          _healthCache.set(b, { ok: false, ts: Date.now() });
          base = null; // 下一轮重选
        }
      }
      // 整轮失败：热身 + 等待 + 重新挑
      await warmUp(bases).catch(() => {});
      await new Promise(r => setTimeout(r, 800));
      base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    }

    throw lastErr || new Error('请求失败');
  }async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
  const bases = resolveApiBases(apiBaseOrBases);
  if (!bases.length) throw new Error('未配置后端 API 地址');

  const bodyRaw = typeof rawPayload === 'string' ? rawPayload : JSON.stringify(payload);

  const containsDataUrl = /data:[^;]+;base64,/.test(bodyRaw);
  if (containsDataUrl || bodyRaw.length > 300000) {
    throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
  }

  let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
  if (!base) {
    base = bases[0];
    void warmUp(bases).catch(() => {});
  }

  const urlFor = (b) => `${b.replace(/\/$/, '')}/${path.replace(/^\/+/, '')}`; // ← 没有 u

  let lastErr = null;
  for (let attempt = 0; attempt <= retry; attempt += 1) {
    const tryOrder = base ? [base, ...bases.filter((x) => x !== base)] : [...bases];
    for (const b of tryOrder) {
      try {
        const res = await fetch(urlFor(b), {
          method: 'POST',
          mode: 'cors',
          cache: 'no-store',
          credentials: 'omit',
          headers: { 'Content-Type': 'application/json' },
          body: bodyRaw,
        });
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `HTTP ${res.status}`);
        }
        _healthCache.set(b, { ok: true, ts: Date.now() });
        return res;
      } catch (err) {
        lastErr = err;
        _healthCache.set(b, { ok: false, ts: Date.now() });
        base = null;
      }
    }
    try { await warmUp(bases, { timeoutMs: 2500 }); } catch {}
    await new Promise((r) => setTimeout(r, 800));
    base = await pickHealthyBase(bases, { timeoutMs: 2500 });
  }

  throw lastErr || new Error('请求失败');
}

  // ---------- 导出到命名空间 ----------
  window.MPoster = {
    // 供 app.js 使用的公共 API：
    resolveApiBases,
    warmUp,
    pickHealthyBase,
    postJsonWithRetry,

    // 可选：如果需要单独调用
    isHealthy,
  };
})();
