
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
    let base = '';
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
