/* placeholder.js — Worker/Render 探活 + 选择 + 重试
 * 仅暴露 window.MPoster；并在存在 window.App.utils 时按需挂载同名方法（不覆盖）
 */
(() => {
  'use strict';

  // ---------------- 常量与缓存 ----------------
  const HEALTH_CACHE = new Map();       // key=base, val={ ok:boolean, ts:number }
  const HEALTH_CACHE_TTL = 60_000;      // 60s

  // ---------------- 小工具 ----------------
  const _tryParse = (url) => { try { return new URL(url, window.location.href); } catch { return null; } };
  const _trimEndSlash = (s) => (s || '').replace(/\/+$/, '');
  const _trimStartSlash = (s) => (s || '').replace(/^\/+/, '');
  const _join = (base, path) => {
    const b = _trimEndSlash(base), p = _trimStartSlash(path);
    return b && p ? `${b}/${p}` : (b || p || '');
  };

  function normalizeBase(base) {
    if (!base) return null;
    const u = _tryParse(base);
    if (!u) return null;
    const pathname = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
    return `${u.origin}${pathname}`;
  }

  function resolveApiBases(input) {
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

  // ---------------- 按域名决定“探活计划” ----------------
  function healthPlanFor(base) {
    const u = _tryParse(base);
    const host = (u && u.host) || '';

    // Render：/health 存在但大多无 CORS 头，先 no-cors
    if (/(^|\.)onrender\.com$/i.test(host)) {
      return [
        { path: '/health',     mode: 'no-cors' }, // 真正健康检查
        { path: '/api/health', mode: 'cors'    }, // 兼容备用
      ];
    }

    // Cloudflare Worker / 你的代理域名：通常 /api/health 有 CORS
    if (/(workers\.dev|cloudflare|render-proxy|cf-)/i.test(host)) {
      return [
        { path: '/api/health', mode: 'cors'    },
        { path: '/health',     mode: 'no-cors' },
      ];
    }

    // 其他未知域：两种都试一次
    return [
      { path: '/api/health', mode: 'cors'    },
      { path: '/health',     mode: 'no-cors' },
    ];
  }

  // ---------------- 探活（带缓存、允许 opaque） ----------------
  async function probeBase(base, { force = false, timeoutMs = 2500 } = {}) {
    const b = normalizeBase(base);
    if (!b) return false;

    const now = Date.now();
    const cached = HEALTH_CACHE.get(b);
    if (!force && cached && now - cached.ts < HEALTH_CACHE_TTL) {
      return cached.ok;
    }

    const plan = healthPlanFor(b);

    // 简易超时
    const withTimeout = (url, mode) => {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort('timeout'), timeoutMs);
      return fetch(url, { method: 'GET', mode, cache: 'no-store', credentials: 'omit', signal: ctrl.signal })
        .finally(() => clearTimeout(t));
    };

    for (const step of plan) {
      const url = _join(b, step.path);
      try {
        const res = await withTimeout(url, step.mode);
        // 允许 opaque（no-cors）作为“可达”
        if (res.ok || res.type === 'opaque') {
          HEALTH_CACHE.set(b, { ok: true, ts: Date.now() });
          return true;
        }
      } catch (err) {
        // 继续尝试下一条
        console.warn('[probeBase] failed', b, step.path, err);
      }
    }

    HEALTH_CACHE.set(b, { ok: false, ts: Date.now() });
    return false;
  }

  // ---------------- 并发暖场 ----------------
  async function warmUp(candidates, { timeoutMs = 2500, useCache = true } = {}) {
    const bases = resolveApiBases(candidates);
    if (!bases.length) return { healthy: [], unhealthy: [] };

    const now = Date.now();
    const tasks = bases.map(async (base) => {
      const cached = HEALTH_CACHE.get(base);
      if (useCache && cached && now - cached.ts < HEALTH_CACHE_TTL) {
        return { base, ok: cached.ok, source: 'cache' };
      }
      const ok = await probeBase(base, { force: true, timeoutMs }).catch(() => false);
      return { base, ok, source: 'probe' };
    });

    const results = await Promise.all(tasks);
    return {
      healthy: results.filter(r => r.ok).map(r => r.base),
      unhealthy: results.filter(r => !r.ok).map(r => r.base),
    };
  }

  // ---------------- 选择健康基址 ----------------
  async function pickHealthyBase(candidates, opts = {}) {
    const bases = resolveApiBases(candidates);
    if (!bases.length) return null;

    // 先用缓存命中
    const now = Date.now();
    const cachedHit = bases.find(b => {
      const c = HEALTH_CACHE.get(b);
      return c && c.ok && now - c.ts < HEALTH_CACHE_TTL;
    });
    if (cachedHit) return cachedHit;

    // 无缓存则并发探活
    const { healthy } = await warmUp(bases, opts);
    if (healthy.length) return healthy[0];

    // 全部失败：回退到第一个，以便错误可观测
    return bases[0] || null;
  }

  // ---------------- POST JSON（自动回退 + 重试） ----------------
  async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) throw new Error('未配置后端 API 地址');

    const bodyRaw = typeof rawPayload === 'string' ? rawPayload : JSON.stringify(payload);

    // 保护：避免把 base64 图片塞进请求体
    if (/data:[^;]+;base64,/.test(bodyRaw) || bodyRaw.length > 300_000) {
      throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
    }

    const urlFor = (b) => _join(b, path);

    let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    if (!base) {
      base = bases[0];
      // 背景并发热身，让下一轮可能命中 cache
      void warmUp(bases).catch(() => {});
    }

    let lastErr = null;

    for (let attempt = 0; attempt <= retry; attempt += 1) {
      const order = base ? [base, ...bases.filter(x => x !== base)] : [...bases];

      for (const b of order) {
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
            const txt = await res.text().catch(() => '');
            throw new Error(txt || `HTTP ${res.status}`);
          }
          HEALTH_CACHE.set(b, { ok: true, ts: Date.now() });
          return res;
        } catch (err) {
          lastErr = err;
          HEALTH_CACHE.set(b, { ok: false, ts: Date.now() });
          base = null; // 下一轮需要重新挑
        }
      }

      // 一轮都失败：暖场 + 等待 + 重新挑
      try { await warmUp(bases, { timeoutMs: 2500 }); } catch {}
      await new Promise(r => setTimeout(r, 800));
      base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    }

    throw lastErr || new Error('请求失败');
  }

  // ---------------- 导出命名空间 ----------------
  const MPoster = {
    // 主 API
    resolveApiBases,
    warmUp,
    pickHealthyBase,
    postJsonWithRetry,
    // 若有需要，可单独拿来用
    probeBase,
  };

  window.MPoster = MPoster;

  // ---------------- 兼容旧代码（按需挂载到 App.utils，不覆盖已存在实现） ----------------
  if (window.App && typeof window.App === 'object') {
    App.utils = App.utils || {};
    App.utils.warmUp = App.utils.warmUp || MPoster.warmUp;
    App.utils.pickHealthyBase = App.utils.pickHealthyBase || MPoster.pickHealthyBase;
    App.utils.postJsonWithRetry = App.utils.postJsonWithRetry || MPoster.postJsonWithRetry;
  }
})();
