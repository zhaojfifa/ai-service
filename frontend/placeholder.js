/* ======= 极简占位版 app.js（可直接部署）======= */

/** 默认候选基址（可按需调整顺序）*/
const WORKER_BASE = 'https://render-proxy.zhaojiffa.workers.dev';
const RENDER_BASE = 'https://ai-service-x758.onrender.com';

/** UI 中“后端地址”输入框（可为空） */
const apiBaseInput = document.getElementById('api-base');

/** 取候选基址：UI 指定 > Worker > Render */
function getApiCandidates() {
  const ui = (apiBaseInput?.value || '').trim();
  return [ui, WORKER_BASE, RENDER_BASE].filter(Boolean);
}

/** 简易超时 fetch */
function fetchWithTimeout(url, init = {}, timeoutMs = 4000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch(url, { ...init, signal: ctrl.signal })
    .finally(() => clearTimeout(t));
}

/** 探测一个 base 是否健康：优先 /api/health，其次 /health */
async function isHealthy(base, timeoutMs = 2000) {
  if (!base) return false;
  const normalized = base.replace(/\/+$/, '');
  const paths = ['/api/health', '/health'];
  for (const p of paths) {
    try {
      const res = await fetchWithTimeout(`${normalized}${p}`, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-store',
        credentials: 'omit',
      }, timeoutMs);
      if (res.ok) return true;
    } catch (_) {
      // ignore, try next path
    }
  }
  return false;
}

/** 健康缓存，减少反复探测 */
const _healthCache = new Map(); // base -> { ok, ts }
const HEALTH_TTL = 60_000;

/** 并发预热（探测） */
async function warmUp(apiBaseOrBases, opts = {}) {
  const bases = resolveApiBases(apiBaseOrBases);
  if (!bases.length) return { healthy: [], unhealthy: [] };

  const now = Date.now();
  const timeoutMs = Number(opts.timeoutMs ?? 2000);

  const tasks = bases.map(async (b) => {
    const cached = _healthCache.get(b);
    if (cached && now - cached.ts < HEALTH_TTL) {
      return { base: b, ok: cached.ok, source: 'cache' };
    }
    const ok = await isHealthy(b, timeoutMs);
    _healthCache.set(b, { ok, ts: Date.now() });
    return { base: b, ok, source: 'probe' };
  });

  const results = await Promise.all(tasks);
  const healthy = results.filter(r => r.ok).map(r => r.base);
  const unhealthy = results.filter(r => !r.ok).map(r => r.base);
  return { healthy, unhealthy };
}

/** 解析候选 */
function resolveApiBases(input) {
  const ui = (apiBaseInput?.value || '').trim();
  const manual = Array.isArray(input) ? input.join(',') : (input || '');
  const merged = [manual, ui, WORKER_BASE, RENDER_BASE]
    .join(',')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  const seen = new Set();
  const out = [];
  for (const b of merged) {
    const norm = b.replace(/\/+$/, '');
    if (!seen.has(norm)) {
      seen.add(norm);
      out.push(norm);
    }
  }
  return out;
}

/** 选择健康基址（先用缓存命中，否则并发探测；都不健康就返回第一个做可观测失败） */
async function pickHealthyBase(apiBaseOrBases, opts = {}) {
  const bases = resolveApiBases(apiBaseOrBases);
  if (!bases.length) return null;

  const now = Date.now();
  const cached = bases.find(b => {
    const c = _healthCache.get(b);
    return c && c.ok && now - c.ts < HEALTH_TTL;
  });
  if (cached) return cached;

  const { healthy } = await warmUp(bases, { timeoutMs: opts.timeoutMs ?? 2000 });
  return healthy[0] || bases[0] || null;
}

/**
 * POST（自动重试 + 回退）
 * @param apiBaseOrBases  可以是候选基址（字符串|数组），也可以直接传绝对 URL
 * @param pathOrUrl       相对路径（如 '/api/generate-poster'）或绝对 URL
 * @param payload         JS 对象
 * @param retry           重试次数（默认 1，即最多请求 2 轮）
 */
async function postJsonWithRetry(apiBaseOrBases, pathOrUrl, payload, retry = 1) {
  const body = JSON.stringify(payload ?? {});
  const tooLarge = body.length > 300_000 || /data:[^;]+;base64,/.test(body);
  if (tooLarge) {
    throw new Error('请求体过大或包含 base64 图片，请改用对象存储的 key/url。');
  }

  // 如果 pathOrUrl 是绝对 URL，直接照它发；否则用健康基址拼接
  const absolute = /^(https?:)?\/\//i.test(pathOrUrl);
  const urlFor = async () => {
    if (absolute) return pathOrUrl;
    const base = await pickHealthyBase(apiBaseOrBases);
    if (!base) throw new Error('无可用后端基址');
    return `${base.replace(/\/+$/, '')}/${String(pathOrUrl).replace(/^\/+/, '')}`;
  };

  let lastErr = null;
  for (let round = 0; round <= retry; round += 1) {
    try {
      const url = await urlFor();
      const res = await fetch(url, {
        method: 'POST',
        mode: 'cors',
        cache: 'no-store',
        credentials: 'omit',
        headers: { 'Content-Type': 'application/json' },
        body,
      });
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(text || `HTTP ${res.status}`);
      }
      return res;
    } catch (err) {
      lastErr = err;
      // 本轮失败，预热一遍再继续
      try { await warmUp(apiBaseOrBases); } catch {}
      await new Promise(r => setTimeout(r, 600));
    }
  }
  throw lastErr || new Error('请求失败');
}

/* ---------- 一点点可选的 UI 辅助（存在就用，不存在忽略） ---------- */
(function boot() {
  const stored = localStorage.getItem('marketing-poster-api-base');
  if (apiBaseInput && !apiBaseInput.value) {
    apiBaseInput.value = stored || WORKER_BASE;
  }
  apiBaseInput?.addEventListener('change', () => {
    const v = apiBaseInput.value.trim();
    if (v) localStorage.setItem('marketing-poster-api-base', v);
  });
})();

/* ---------- 对外导出，方便旧代码直接复用 ---------- */
window.MPoster = {
  WORKER_BASE,
  RENDER_BASE,
  getApiCandidates,
  resolveApiBases,
  warmUp,
  pickHealthyBase,
  isHealthy,
  postJsonWithRetry,
};
