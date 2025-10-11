
/* ==========================================================================
 * Marketing Poster App - Placeholder Integration Build
 * ========================================================================== */
(function () {
  'use strict';

  const WORKER_BASE = 'https://render-proxy.zhaojiffa.workers.dev';
  const RENDER_BASE = 'https://ai-service-x758.onrender.com';

  const STORAGE_KEYS = {
    apiBase: 'marketing-poster-api-base',
    stage1: 'marketing-poster-stage1-data',
    stage2: 'marketing-poster-stage2-result',
  };

  const apiBaseInput = document.getElementById('api-base');
  function setStatus(el, msg, level = 'info') {
    if (!el) return;
    el.textContent = msg;
    el.className = level ? `status-${level}` : '';
  }

  function assetUrl(path) {
    if (!path) return path;
    if (/^(https?:)?\/\//i.test(path) || path.startsWith('data:')) return path;
    let base = // ===== Worker / Render 候选基址 =====
const WORKER_BASE = 'https://render-proxy.zhaojiffa.workers.dev';
const RENDER_BASE = 'https://ai-service-x758.onrender.com';

// 从输入框/本地存储读取的地址，也和上面两个一起做候选
function getApiCandidates() {
  const uiBase = (apiBaseInput?.value || '').trim();
  // 顺序：UI 指定 > Worker > Render（可根据需要换顺序）
  return [uiBase, WORKER_BASE, RENDER_BASE].filter(Boolean);
}

const STORAGE_KEYS = {
  apiBase: 'marketing-poster-api-base',
  stage1: 'marketing-poster-stage1-data',
  stage2: 'marketing-poster-stage2-result',
};

const DEFAULT_STAGE1 = {
  brand_name: '厨匠ChefCraft',
  agent_name: '星辉渠道服务中心',
  scenario_image: '现代开放式厨房中智能蒸烤一体机的沉浸式体验',
  product_name: 'ChefCraft 智能蒸烤大师',
  template_id: 'template_dual',
  scenario_mode: 'upload',
  product_mode: 'upload',
  features: [
    '一键蒸烤联动，精准锁鲜',
    '360° 智能热风循环，均匀受热',
    '高温自清洁腔体，省心维护',
    'Wi-Fi 远程操控，云端菜谱推送',
  ],
  title: '焕新厨房效率，打造大厨级美味',
  subtitle: '智能蒸烤 · 家宴轻松掌控',
};

const TEMPLATE_REGISTRY_PATH = 'templates/registry.json';
const templateCache = new Map();
let templateRegistryPromise = null;

const PROMPT_PRESETS_PATH = 'prompts/presets.json';
let promptPresetPromise = null;
const PROMPT_SLOTS = ['scenario', 'product', 'gallery'];
const DEFAULT_PROMPT_VARIANTS = 1;

const DEFAULT_EMAIL_RECIPIENT = 'client@example.com';

const galleryPlaceholderCache = new Map();

const MATERIAL_DEFAULT_LABELS = {
  brand_logo: '品牌 Logo',
  scenario: '应用场景图',
  product: '主产品渲染图',
  gallery: '底部产品小图',
};

// =====================================
// 统一网络模块（幂等加载，挂载到 window.NET）
// =====================================
(function () {
  const ns = (window.__posterNet = window.__posterNet || {});

  if (!ns.resolveApiBases) {
    ns.resolveApiBases = function resolveApiBases(input) {
      const manual = typeof input === 'string'
        ? input
        : Array.isArray(input)
          ? input.join(',')
          : '';
      const fromInput = (window.apiBaseInput?.value || '').trim();
      const merged = [manual, fromInput]
        .join(',')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const seen = new Set();
      const bases = [];
      merged.forEach((b) => {
        const norm = b.replace(/\/+$/, '');
        if (!seen.has(norm)) {
          seen.add(norm);
          bases.push(norm);
        }
      });
      return bases;
    };
  }

  ns._healthCache = ns._healthCache || new Map();
  ns.HEALTH_TTL_MS = ns.HEALTH_TTL_MS || 60 * 1000;

  if (!ns.warmUp) {
    ns.warmUp = async function warmUp(apiBaseOrBases, opts = {}) {
      const bases = ns.resolveApiBases(apiBaseOrBases);
      if (!bases.length) return { healthy: [], unhealthy: [] };

      const {
        paths = ['/api/health', '/health'],
        timeoutMs = 2500,
        useCache = true,
      } = opts;

      const controller = (ms) => {
        const c = new AbortController();
        const t = setTimeout(() => c.abort('timeout'), ms);
        return { signal: c.signal, cancel: () => clearTimeout(t) };
      };

      const now = Date.now();
      const tasks = bases.map(async (base) => {
        const cached = ns._healthCache.get(base);
        if (useCache && cached && now - cached.ts < ns.HEALTH_TTL_MS) {
          return { base, ok: cached.ok, source: 'cache' };
        }
        let ok = false;
        for (const p of paths) {
          const { signal, cancel } = controller(timeoutMs);
          try {
            const res = await fetch(`${base}${p}`, {
              method: 'GET',
              mode: 'cors',
              cache: 'no-store',
              credentials: 'omit',
              signal,
            });
            cancel();
            if (res.ok) { ok = true; break; }
          } catch {}
        }
        ns._healthCache.set(base, { ok, ts: Date.now() });
        return { base, ok, source: 'probe' };
      });

      const results = await Promise.all(tasks);
      const healthy = results.filter((r) => r.ok).map((r) => r.base);
      const unhealthy = results.filter((r) => !r.ok).map((r) => r.base);
      return { healthy, unhealthy };
    };
  }

  if (!ns.pickHealthyBase) {
    ns.pickHealthyBase = async function pickHealthyBase(apiBaseOrBases, opts = {}) {
      const bases = ns.resolveApiBases(apiBaseOrBases);
      if (!bases.length) return null;

      const cachedHealthy = bases.filter((b) => {
        const c = ns._healthCache.get(b);
        return c && c.ok && Date.now() - c.ts < ns.HEALTH_TTL_MS;
      });
      if (cachedHealthy.length) return cachedHealthy[0];

      const { healthy } = await ns.warmUp(bases, opts);
      return healthy[0] || null;
    };
  }

  if (!ns.postJsonWithRetryNew) {
    ns.postJsonWithRetryNew = async function postJsonWithRetryNew(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
      const bases = ns.resolveApiBases(apiBaseOrBases);
      if (!bases.length) throw new Error('未配置后端 API 地址');
      const bodyRaw = typeof rawPayload === 'string' ? rawPayload : JSON.stringify(payload);
      const containsDataUrl = /data:[^;]+;base64,/.test(bodyRaw);
      if (containsDataUrl || bodyRaw.length > 300000) {
        throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传输 key/url。');
      }

      let base = await ns.pickHealthyBase(bases, { timeoutMs: 2500 });
      if (!base) { base = bases[0]; void ns.warmUp(bases).catch(() => {}); }

      const urlFor = (b) => `${b.replace(/\/$/, '')}/${path.replace(/^\/+/, '')}`;
      let lastErr = null;

      for (let attempt = 0; attempt <= retry; attempt += 1) {
        const tryOrder = base ? [base, ...bases.filter((b) => b !== base)] : [...bases];
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
            ns._healthCache.set(b, { ok: true, ts: Date.now() });
            return res;
          } catch (err) {
            lastErr = err;
            ns._healthCache.set(b, { ok: false, ts: Date.now() });
            base = null;
          }
        }
        try { await ns.warmUp(bases, { timeoutMs: 2500 }); } catch {}
        await new Promise((r) => setTimeout(r, 800));
        base = await ns.pickHealthyBase(bases, { timeoutMs: 2500 });
      }
      throw lastErr || new Error('请求失败');
    };
  }

  // 兼容旧签名：postJsonWithRetry(完整URL, payload)
  window.postJsonWithRetry = window.postJsonWithRetry || async function postJsonWithRetry(urlOrBase, payload, retry = 1, rawPayload) {
    if (typeof urlOrBase === 'string') {
      const m = urlOrBase.match(/^https?:\/\/[^/]+/i);
      if (m) {
        const base = m[0];
        const path = urlOrBase.slice(base.length) || '/';
        return ns.postJsonWithRetryNew(base, path, payload, retry, rawPayload);
      }
      return ns.postJsonWithRetryNew(urlOrBase, '/api/generate-poster', payload, retry, rawPayload);
    }
    return ns.postJsonWithRetryNew(urlOrBase, '/api/generate-poster', payload, retry, rawPayload);
  };

  window.NET = window.NET || {};
  Object.assign(window.NET, {
    resolveApiBases: ns.resolveApiBases,
    warmUp: ns.warmUp,
    pickHealthyBase: ns.pickHealthyBase,
    postJsonWithRetry: ns.postJsonWithRetryNew,
  });
})();

// =======================
// 其余应用逻辑（占位/示例）
// =======================

const placeholderImages = {
  brandLogo: createPlaceholder('品牌\\nLogo'),
  scenario: createPlaceholder('应用场景'),
  product: createPlaceholder('产品渲染'),
};

const assetStore = createAssetStore();

function getPosterImageSource(image) {
  if (!image || typeof image !== 'object') return '';
  const directUrl = typeof image.url === 'string' ? image.url : '';
  if (directUrl) return directUrl;
  const dataUrl = typeof image.data_url === 'string' ? image.data_url : '';
  return dataUrl;
}

function assignPosterImage(element, image, altText) {
  if (!element) return false;
  const src = getPosterImageSource(image);
  if (!src) return false;
  element.src = src;
  if (altText) {
    element.alt = altText;
  }
  return true;
}

async function r2PresignPut(folder, file) {
  const candidates = getApiCandidates();
  const base = await NET.pickHealthyBase(candidates);
  if (!base) throw new Error('未配置后端 API 地址，无法上传至 R2。');

  const endpoint = `${base.replace(/\/$/, '')}/api/r2/presign-put`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      folder,
      filename: file.name || 'upload.png',
      content_type: file.type || 'application/octet-stream',
      size: typeof file.size === 'number' ? file.size : null,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || '获取 R2 上传授权失败。');
  }
  return response.json();
}

async function uploadFileToR2(folder, file) {
  const presign = await r2PresignPut(folder, file);
  const response = await fetch(presign.put_url, {
    method: 'PUT',
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    body: file,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || '上传到 R2 失败，请稍后重试。');
  }
  return presign;
}

// ------------------------
// 页面初始化占位
// ------------------------

const apiBaseInput = document.getElementById('api-base');

init();

function init() {
  loadApiBase();
  if (apiBaseInput) {
    apiBaseInput.addEventListener('change', saveApiBase);
    apiBaseInput.addEventListener('blur', saveApiBase);
  }
}

function loadApiBase() {
  if (!apiBaseInput) return;
  const stored = localStorage.getItem(STORAGE_KEYS.apiBase);
  apiBaseInput.value = (stored && stored.trim()) || WORKER_BASE; // 默认 Worker
}

function saveApiBase() {
  if (!apiBaseInput) return;
  const value = apiBaseInput.value.trim();
  if (value) {
    localStorage.setItem(STORAGE_KEYS.apiBase, value);
  } else {
    localStorage.removeItem(STORAGE_KEYS.apiBase);
  }
}

// 简化的工具函数与占位实现（请在实际项目中替换为完整版本）
function createPlaceholder(text){return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='420' height='300'><rect width='420' height='300' fill='#e5e9f0'/><rect x='16' y='16' width='388' height='268' rx='24' fill='none' stroke='#cbd2d9' stroke-width='4' stroke-dasharray='12 10'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='#3d4852' font-size='26' font-family='Segoe UI,Noto Sans,sans-serif' font-weight='600'>${text}</text></svg>`)}`; }
function setStatus(el,msg,level='info'){ if(!el) return; el.textContent=msg; el.className=level?`status-${level}`:''; }

function createAssetStore(){
  const memory = new Map();
  return {
    async put(k,v){memory.set(k,v); return k;},
    async get(k){return memory.get(k)||null;},
    async delete(k){memory.delete(k);},
    async clear(){memory.clear();}
  };
}

    const baseEl = document.querySelector('base[href]');
    if (baseEl) {
      base = baseEl.getAttribute('href') || '';
    } else {
      const { origin, pathname } = window.location;
      const parts = pathname.split('/').filter(Boolean);
      base = parts.length > 0 ? `${origin}/${parts[0]}/` : `${origin}/`;
    }
    return new URL(path.replace(/^\//, ''), base).toString();
  }

  function loadApiBase() {
    if (!apiBaseInput) return;
    const stored = localStorage.getItem(STORAGE_KEYS.apiBase);
    apiBaseInput.value = (stored && stored.trim()) || WORKER_BASE;
  }
  function saveApiBase() {
    if (!apiBaseInput) return;
    const v = apiBaseInput.value.trim();
    if (v) localStorage.setItem(STORAGE_KEYS.apiBase, v);
    else localStorage.removeItem(STORAGE_KEYS.apiBase);
  }
  function getApiCandidates() {
    const ui = (apiBaseInput?.value || '').trim();
    return [ui, WORKER_BASE, RENDER_BASE].filter(Boolean);
  }

  const _healthCache = new Map();
  const HEALTH_TTL_MS = 60 * 1000;

  function resolveApiBases(input) {
    const ui = (apiBaseInput?.value || '').trim();
    const list = [Array.isArray(input) ? input.join(',') : (input || ''), ui]
      .join(',')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);
    const out = [];
    const seen = new Set();
    list.forEach(b => {
      const norm = b.replace(/\/+$/g, '');
      if (!seen.has(norm)) { seen.add(norm); out.push(norm); }
    });
    return out;
  }

  function controller(timeoutMs) {
    const c = new AbortController();
    const t = setTimeout(() => c.abort('timeout'), timeoutMs);
    return { signal: c.signal, cancel: () => clearTimeout(t) };
  }

  async function warmUp(apiBaseOrBases, opts = {}) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) return { healthy: [], unhealthy: [] };
    const { paths = ['/api/health', '/health'], timeoutMs = 2500, useCache = true } = opts;
    const now = Date.now();
    const tasks = bases.map(async (base) => {
      const cached = _healthCache.get(base);
      if (useCache && cached && now - cached.ts < HEALTH_TTL_MS) {
        return { base, ok: cached.ok, source: 'cache' };
      }
      let ok = false;
      for (const p of paths) {
        const { signal, cancel } = controller(timeoutMs);
        try {
          const res = await fetch(`${base}${p}`, {
            method: 'GET', mode: 'cors', cache: 'no-store', credentials: 'omit', signal,
          });
          cancel();
          if (res.ok) { ok = true; break; }
        } catch (e) {}
      }
      _healthCache.set(base, { ok, ts: Date.now() });
      return { base, ok, source: 'probe' };
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
    const cached = bases.filter(b => {
      const c = _healthCache.get(b);
      return c && c.ok && Date.now() - c.ts < HEALTH_TTL_MS;
    });
    if (cached.length) return cached[0];
    const { healthy } = await warmUp(bases, opts);
    return healthy[0] || bases[0] || null;
  }

  function encodeJson(obj) {
    return typeof obj === 'string' ? obj : JSON.stringify(obj);
  }

  async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawOverride) {
    const bases = resolveApiBases(apiBaseOrBases);
    if (!bases.length) throw new Error('未配置后端 API 地址');

    const raw = typeof rawOverride === 'string' ? rawOverride : encodeJson(payload);
    const containsDataUrl = /data:[^;]+;base64,/.test(raw);
    if (containsDataUrl || raw.length > 300000) {
      throw new Error('请求体过大或包含 base64 图片，请先直传素材（仅传 key/url）。');
    }

    let base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    if (!base) {
      base = bases[0];
      void warmUp(bases).catch(() => {});
    }

    const urlFor = (b) => `${b.replace(/\/$/, '')}/${path.replace(/^\/+/, '')}`;
    let lastErr = null;

    for (let attempt = 0; attempt <= retry; attempt += 1) {
      const tryOrder = base ? [base, ...bases.filter(b => b !== base)] : [...bases];
      for (const b of tryOrder) {
        try {
          const res = await fetch(urlFor(b), {
            method: 'POST',
            mode: 'cors',
            cache: 'no-store',
            credentials: 'omit',
            headers: { 'Content-Type': 'application/json' },
            body: raw,
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
      await new Promise(r => setTimeout(r, 800));
      base = await pickHealthyBase(bases, { timeoutMs: 2500 });
    }
    throw lastErr || new Error('请求失败');
  }

  async function r2PresignPut(folder, file) {
    const base = await pickHealthyBase(getApiCandidates());
    if (!base) throw new Error('未配置后端 API 地址，无法上传至 R2。');
    const endpoint = `${base.replace(/\/$/, '')}/api/r2/presign-put`;
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder,
        filename: file.name || 'upload.png',
        content_type: file.type || 'application/octet-stream',
        size: typeof file.size === 'number' ? file.size : null,
      }),
    });
    if (!resp.ok) throw new Error(await resp.text() || '获取 R2 上传授权失败。');
    return resp.json();
  }

  async function uploadFileToR2(folder, file) {
    const presign = await r2PresignPut(folder, file);
    const put = await fetch(presign.put_url, {
      method: 'PUT',
      headers: { 'Content-Type': file.type || 'application/octet-stream' },
      body: file,
    });
    if (!put.ok) throw new Error(await put.text() || '上传到 R2 失败');
    return presign;
  }

  async function init() {
    loadApiBase();
    if (apiBaseInput) {
      apiBaseInput.addEventListener('change', saveApiBase);
      apiBaseInput.addEventListener('blur', saveApiBase);
    }
    void warmUp(getApiCandidates()).catch(() => {});
    const stage = document.body?.dataset?.stage;
    if (stage === 'stage1') initStage1();
    else if (stage === 'stage2') initStage2();
    else if (stage === 'stage3') initStage3();
  }

  function initStage1() {
    console.info('[App] Stage1 init (placeholder)');
    const status = document.getElementById('stage1-status');
    setStatus(status, '占位版：请接入真实模板选择与预览逻辑。', 'info');
  }

  function initStage2() {
    console.info('[App] Stage2 init (placeholder)');
    const status = document.getElementById('stage2-status');
    setStatus(status, '占位版：点击“生成”将调用 /api/generate-poster。', 'info');
    const btn = document.getElementById('generate-poster');
    if (btn) {
      btn.addEventListener('click', async () => {
        try {
          const base = await pickHealthyBase(getApiCandidates());
          if (!base) throw new Error('后端不可用');
          const res = await postJsonWithRetry(base, '/api/generate-poster', { demo: true }, 1);
          const data = await res.json().catch(() => ({}));
          console.log('[App] response:', data);
          setStatus(status, '占位请求完成。', 'success');
        } catch (e) {
          console.error(e);
          setStatus(status, e.message || '失败', 'error');
        }
      });
    }
  }

  function initStage3() {
    console.info('[App] Stage3 init (placeholder)');
    const status = document.getElementById('stage3-status');
    setStatus(status, '占位版：点击“发送”将调用 /api/send-email。', 'info');
    const btn = document.getElementById('send-email');
    if (btn) {
      btn.addEventListener('click', async () => {
        try {
          const base = await pickHealthyBase(getApiCandidates());
          if (!base) throw new Error('后端不可用');
          await postJsonWithRetry(base, '/api/send-email', {
            recipient: 'client@example.com',
            subject: 'Demo',
            body: 'Demo body',
            attachment: null,
          }, 1);
          setStatus(status, '占位发送成功。', 'success');
        } catch (e) {
          console.error(e);
          setStatus(status, e.message || '失败', 'error');
        }
      });
    }
  }

  window.App = {
    init,
    utils: {
      assetUrl,
      warmUp,
      pickHealthyBase,
      postJsonWithRetry,
      uploadFileToR2,
      r2PresignPut,
      getApiCandidates,
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
