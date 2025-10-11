/* placeholder.js — Worker/Render 探活 + 选择 + 重试（仅此文件）
   1) 对 onrender.com 的 /health 采用 no-cors 探活并视为健康
   2) 向 window 和 App.utils 兜底导出，避免 app.js 报未定义
*/
(() => {
  'use strict';

  // ---------- 小工具 ----------
  function _tryURL(input) {
    try { return new URL(input, location.href); } catch { return null; }
  }
  function _normalizeBase(base) {
    if (!base) return null;
    const u = _tryURL(base);
    if (!u) return null;
    const p = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
    return `${u.origin}${p}`;
  }
  function _join(base, path) {
    const b = (base || '').replace(/\/+$/, '');
    const p = (path || '').replace(/^\/+/, '');
    return b && p ? `${b}/${p}` : (b || p || '');
  }

  // 解析候选基址：字符串 / 逗号分隔 / 数组 都行；去重+标准化
  function resolveApiBases(input) {
    const merged = Array.isArray(input) ? input.join(',') : (input || '');
    const out = [];
    const seen = new Set();
    merged.split(',').map(s => s.trim()).filter(Boolean).forEach(b => {
      const n = _normalizeBase(b);
      if (n && !seen.has(n)) { seen.add(n); out.push(n); }
    });
    return out;
  }

  // ---------- 探活策略 ----------
  // 针对域名生成探活“计划”：path + fetch.mode
  function _healthPlanFor(base) {
    const u = _tryURL(base);
    const host = (u && u.host) || '';

    // Render 常见：/health 可访问但无 CORS 头；用 no-cors 即可“通电”判断
    if (/(^|\.)onrender\.com$/i.test(host)) {
      return [
        { path: '/health',     mode: 'no-cors' },
        { path: '/api/health', mode: 'cors'    },
      ];
    }

    // Cloudflare Worker 或自建代理：通常 /api/health 带 CORS
    if (/(workers\.dev|render-proxy|cloudflare|cf-)/i.test(host)) {
      return [
        { path: '/api/health', mode: 'cors'    },
        { path: '/health',     mode: 'no-cors' },
      ];
    }

    // 其他：都试一遍
    return [
      { path: '/api/health', mode: 'cors'    },
      { path: '/health',     mode: 'no-cors' },
    ];
  }

  const _HEALTH_CACHE = new Map(); // base -> { ok, ts }
  const HEALTH_TTL_MS = 60_000;

  async function isHealthy(base, timeoutMs = 2500) {
    const b = _normalizeBase(base);
    if (!b) return false;

    const controller = ms => {
      const c = new AbortController();
      const t = setTimeout(() => c.abort('timeout'), ms);
      return { signal: c.signal, done: () => clearTimeout(t) };
    };

    for (const plan of _healthPlanFor(b)) {
      const { signal, done } = controller(timeoutMs);
      try {
        const res = await fetch(_join(b, plan.path), {
          method: 'GET',
          mode: plan.mode,           // 关键：Render 用 no-cors
          cache: 'no-store',
          credentials: 'omit',
          signal,
        });
        done();

        // no-cors 的 opaque 响应 status=0/ok=false，但能返回就视为“通”
        if (plan.mode === 'no-cors') return true;
        if (res.ok) return true;
      } catch (_) {
        done();
        // 继续尝试下一个计划
      }
    }
    return false;
  }

  async function warmUp(apiBaseOrBases, { timeoutMs = 2500, useCache = true } = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return { healthy: [], unhealthy: [] };

    const now = Date.now();
    const tasks = bases.map(async b => {
      const cached = _HEALTH_CACHE.get(b);
      if (useCache && cached && now - cached.ts < HEALTH_TTL_MS) {
        return { base: b, ok: cached.ok, source: 'cache' };
      }
      const ok = await isHealthy(b, timeoutMs);
      _HEALTH_CACHE.set(b, { ok, ts: Date.now() });
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
      const c = _HEALTH_CACHE.get(b);
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
      base = bases[0];              // 全不健康也回退到第一个，保持可观测
      void warmUp(bases).catch(() => {});
    }
    const urlFor = b => _join(b, String(path || '').replace(/^\/+/, ''));

    let lastErr = null;
    for (let attempt = 0; attempt <= retry; attempt += 1) {
      const order = base ? [base, ...bases.filter(x => x !== base)] : bases;
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
            const text = await res.text().catch(() => '');
            throw new Error(text || `HTTP ${res.status}`);
          }
          _HEALTH_CACHE.set(b, { ok: true, ts: Date.now() });
          return res;
        } catch (e) {
          lastErr = e;
          _HEALTH_CACHE.set(b, { ok: false, ts: Date.now() });
          base = null; // 下一轮重新挑
        }
      }
      // 一整轮失败：再探活一次，稍等再重试
      try { await warmUp(bases, { timeoutMs: 2500 }); } catch {}
      await new Promise(r => setTimeout(r, 800));
      base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    }
    throw lastErr || new Error('请求失败');
  }

  // ---------- 导出：命名空间 + 全局兜底（兼容 app.js 直接调用裸函数） ----------
  const API = { resolveApiBases, warmUp, pickHealthyBase, postJsonWithRetry, isHealthy };

  // 命名空间
  window.MPoster = Object.assign({}, window.MPoster || {}, API);

  // 全局同名函数兜底（app.js 里直接调用 resolveApiBases 等时可用）
  Object.keys(API).forEach((k) => {
    if (typeof window[k] !== 'function') {
      window[k] = API[k];
    }
  });

  // 也塞进 App.utils（如果存在）
  if (window.App && window.App.utils) {
    Object.keys(API).forEach((k) => {
      if (typeof window.App.utils[k] !== 'function') {
        window.App.utils[k] = API[k];
      }
    });
  }
})();
