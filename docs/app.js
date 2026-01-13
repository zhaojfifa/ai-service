
const App = (window.App ??= {});
App.utils = App.utils ?? {};

const VERTEX_IMAGE_TAG_CLASSNAMES = {
  scenario: 'slot-scenario',
  product: 'slot-product',
  gallery: 'slot-gallery',
};
let apiBaseInput;

// 统一从后端图片对象里拿 src，兼容 vertex/url 和旧的 asset/dataUrl
function pickImageSrc(img) {
  if (!img) return null;
  if (typeof img === 'string') return img;

  const src =
    (typeof img.url === 'string' && img.url.trim()) ||
    (typeof img.asset === 'string' && img.asset.trim()) ||
    (typeof img.dataUrl === 'string' && img.dataUrl.trim()) ||
    (typeof img.data_url === 'string' && img.data_url.trim()) ||
    null;

  return src;
}

function buildGeneratedAssetFromUrl(url, key) {
  if (!url) return null;
  return {
    key: null,
    dataUrl: url,
    remoteUrl: url,
    url,
    r2Key: key || null,
    type: 'image/png',
    size: null,
    lastModified: Date.now(),
  };
}

function applySlotImagePreview(slot, index, url, { logoFallback } = {}) {
  const logoImg = document.getElementById('preview-brand-logo');
  const finalUrl = url || logoFallback || logoImg?.src || '';
  if (!finalUrl) return;

  const selectors = [];
  if (slot === 'gallery') {
    selectors.push(`[data-role="gallery-preview"][data-index="${index}"]`);
    selectors.push(
      `.poster-gallery [data-gallery-index="${index}"] img, .bottom-product-card[data-gallery-index="${index}"] img`
    );
    selectors.push(`#preview-gallery figure:nth-child(${index + 1}) img`);
    selectors.push(`#poster-result .poster-gallery-slot[data-index="${index}"] img`);
  } else if (slot === 'scenario') {
    selectors.push('#preview-scenario-image');
    selectors.push('#poster-result-scenario-image');
  } else if (slot === 'product') {
    selectors.push('#preview-product-image');
    selectors.push('#poster-result-product-image');
  }

  selectors
    .map((selector) => document.querySelectorAll(selector))
    .forEach((nodeList) => {
      nodeList.forEach((img) => {
        if (img && img.tagName === 'IMG') {
          img.src = finalUrl;
          img.style.visibility = 'visible';
        }
      });
    });
}

let lastStage1Data = null;
let lastPosterResult = null;
let posterLayoutRoot = null;

// --- Stage2: 缓存最近一次生成结果，给 A/B 对比、重放使用 ---
const posterGenerationState = {
  /** 海报成品图 URL（R2 的公开地址） */
  posterUrl: null,
  /** 本次生成用到的 prompt 结构，用于展示 / 调试 */
  promptBundle: null,
  /** Vertex / Glibatree 返回的原始响应，必要时可做更多调试 */
  rawResult: null,
};
// 兼容旧版调用：确保引用不存在的全局变量时不会抛出 ReferenceError
let posterGeneratedImage = null;
let posterGeneratedLayout = null;

// stage2：缓存最近一次生成结果与提示词，便于预览与回放
let posterGeneratedImageUrl = null;
let lastPromptBundle = null;

const stage2State = {
  poster: {
    brand_name: '',
    agent_name: '',
    headline: '',
    tagline: '',
    features: [],
    series: [],
    gallery_entries: [],
  },
  assets: {
    brand_logo_url: '',
    scenario_url: '',
    product_url: '',
    gallery_urls: [],
    composite_poster_url: '',
  },
  assetsB: {},
  vertex: {
    lastResponse: null,
  },
  activeVariant: 'A',
};
const DEMO_A_NO_AI_IMAGES = true;
const DEMO_B_AI_IMAGES_TO_ASSETSB = true;
let stage2GenerationSeq = 0;
let stage2InFlight = false;

function setTextIfNonEmpty(el, next, fallback = '') {
  if (!el) return;
  const nextText = typeof next === 'string' ? next.trim() : '';
  if (nextText) {
    el.textContent = nextText;
    return;
  }
  const currentText = typeof el.textContent === 'string' ? el.textContent.trim() : '';
  if (currentText) return;
  if (fallback != null) el.textContent = String(fallback);
}

function setImageSrcIfNonEmpty(imgEl, nextUrl) {
  if (!imgEl) return;
  const url = typeof nextUrl === 'string' ? nextUrl.trim() : '';
  if (!url) return;
  imgEl.src = url;
  if (imgEl.style) {
    imgEl.style.visibility = 'visible';
    if (imgEl.style.display === 'none') {
      imgEl.style.display = '';
    }
  }
}

function setStage2ButtonsDisabled(disabled) {
  const generateButton = document.getElementById('generate-poster');
  const regenerateButton = document.getElementById('regenerate-poster');
  const variantABtn = document.getElementById('variant-a-btn');
  const variantBBtn = document.getElementById('variant-b-btn');
  if (generateButton) generateButton.disabled = disabled;
  if (regenerateButton) regenerateButton.disabled = disabled;
  if (variantABtn) variantABtn.disabled = disabled;
  if (variantBBtn) variantBBtn.disabled = disabled;
}

function rehydrateStage2PosterFromStage1() {
  const snapshot = loadStage1Data() || lastStage1Data || null;
  if (!snapshot) return;
  const poster = stage2State.poster;
  if (!poster.brand_name) poster.brand_name = snapshot.brand_name || '';
  if (!poster.agent_name) poster.agent_name = snapshot.agent_name || '';
  if (!poster.headline) poster.headline = snapshot.title || '';
  if (!poster.tagline) {
    poster.tagline = snapshot.subtitle || snapshot.tagline || snapshot.slogan || '';
  }
  if (!Array.isArray(poster.features) || poster.features.length === 0) {
    poster.features = Array.isArray(snapshot.features)
      ? snapshot.features.filter(Boolean)
      : [];
  }
  if (!Array.isArray(poster.series) || poster.series.length === 0) {
    poster.series = Array.isArray(snapshot.gallery_entries)
      ? snapshot.gallery_entries.filter(Boolean).map((entry) => ({ name: entry.caption || '' }))
      : [];
  }
  if (!Array.isArray(poster.gallery_entries) || poster.gallery_entries.length === 0) {
    poster.gallery_entries = Array.isArray(snapshot.gallery_entries)
      ? snapshot.gallery_entries.filter(Boolean)
      : [];
  }
}
// 双列功能模板的归一化布局（随容器等比缩放）
const TEMPLATE_DUAL_LAYOUT = {
  canvas: { width: 1024, height: 1024 },
  slots: {
    logo: { x: 0.06, y: 0.07, w: 0.08, h: 0.08, type: 'image' },
    brand_name: { x: 0.18, y: 0.08, w: 0.30, h: 0.06, type: 'text', align: 'left' },
    agent_name: { x: 0.54, y: 0.08, w: 0.38, h: 0.08, type: 'text', align: 'right' },

    scenario: { x: 0.05, y: 0.22, w: 0.38, h: 0.44, type: 'image' },
    product: { x: 0.45, y: 0.22, w: 0.48, h: 0.44, type: 'image' },
    headline: { x: 0.08, y: 0.70, w: 0.84, h: 0.08, type: 'text', align: 'center' },

    series_1_img: { x: 0.06, y: 0.80, w: 0.18, h: 0.13, type: 'image' },
    series_1_txt: { x: 0.06, y: 0.93, w: 0.18, h: 0.03, type: 'text', align: 'center' },
    series_2_img: { x: 0.30, y: 0.80, w: 0.18, h: 0.13, type: 'image' },
    series_2_txt: { x: 0.30, y: 0.93, w: 0.18, h: 0.03, type: 'text', align: 'center' },
    series_3_img: { x: 0.54, y: 0.80, w: 0.18, h: 0.13, type: 'image' },
    series_3_txt: { x: 0.54, y: 0.93, w: 0.18, h: 0.03, type: 'text', align: 'center' },
    series_4_img: { x: 0.78, y: 0.80, w: 0.18, h: 0.13, type: 'image' },
    series_4_txt: { x: 0.78, y: 0.93, w: 0.18, h: 0.03, type: 'text', align: 'center' },
    tagline: { x: 0.10, y: 0.96, w: 0.80, h: 0.03, type: 'text', align: 'center' },
  },
};
// 快速自测：在 stage2 页面点击“生成海报与文案”应完成请求且无 posterGenerationState 未定义报错，
// 生成成功后 A/B 对比按钮才可使用。

// 1) 新增：按域名决定健康检查路径
function isRenderHost(base) {
  try {
    const u = new URL(base, location.href);
    return /onrender\.com$/i.test(u.hostname);
  } catch {
    return false;
  }
}

function healthPathsFor(base) {
  // Render 后端只有 /health，且通常无 CORS
  if (isRenderHost(base)) return ['/health'];
  // Worker（或网关）提供 /api/health（带 CORS）
  return ['/api/health', '/health'];
}
// ===== 共享：模板资源助手（全局唯一出口） =====

/** 从 templates/registry.json 读取模板清单（带缓存） */
App.utils.loadTemplateRegistry = (() => {
  let _registryP;
  return async function loadTemplateRegistry() {
    if (!_registryP) {
      _registryP = fetch(App.utils.assetUrl?.('templates/registry.json') || 'templates/registry.json')
        .then(r => {
          if (!r.ok) throw new Error('无法加载模板清单');
          return r.json();
        })
        .then(list => (Array.isArray(list) ? list : []))
        .catch(err => {
          _registryP = null; // 失败时允许下次重试
          throw err;
        });
    }
    return _registryP;
  };
})();

/** 按模板 id 返回 { entry, spec, image }（带缓存） */
App.utils.ensureTemplateAssets = (() => {
  const _cache = new Map();
  return async function ensureTemplateAssets(templateId) {
    if (_cache.has(templateId)) return _cache.get(templateId);

    const registry = await App.utils.loadTemplateRegistry();
    const entry = registry.find(i => i.id === templateId) || registry[0];
    if (!entry) throw new Error('模板列表为空');

    const specUrl = App.utils.assetUrl?.(`templates/${entry.spec}`) || `templates/${entry.spec}`;
    const imgUrl  = App.utils.assetUrl?.(`templates/${entry.preview}`) || `templates/${entry.preview}`;

    const specP = fetch(specUrl).then(r => { if (!r.ok) throw new Error('无法加载模板规范'); return r.json(); });
    const imgP  = new Promise((resolve, reject) => {
      const img = new Image();
      img.decoding = 'async';
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('模板预览图加载失败'));
      img.src = imgUrl;
    });

    const payload = { entry, spec: await specP, image: await imgP };
    _cache.set(entry.id, payload);
    return payload;
  };
})();

const HEALTH_CACHE_TTL = 60_000;
const HEALTH_CACHE = new Map();

let documentAssetBase = null;

//
// 组装 prompts —— 每个槽都是对象
function buildPromptSlot(prefix) {
  return {
    preset:  getValue(`#${prefix}-preset`),     // 你的原有取值方法
    positive:getValue(`#${prefix}-positive`),
    negative:getValue(`#${prefix}-negative`),
    aspect:  getValue(`#${prefix}-aspect`)
  };
}
function buildGeneratePayload() {
  return {
    poster: collectStage1Data(form, state, { strict: false }),
    render_mode: state.renderMode || 'locked',
    variants: Number(state.variants || 2),
    seed: state.seed ?? null,
    lock_seed: !!state.lockSeed,
    prompts: {
      scenario: buildPromptSlot('scenario'),
      product:  buildPromptSlot('product'),
      gallery:  buildPromptSlot('gallery'),
    }
  };
}

// 串行触发，避免免费实例并发卡死
async function runGeneration() {
  setBusy(true);
  try {
    const payloadA = buildGeneratePayload();
    await triggerGeneration(payloadA);   // 先等第一个完成
    if (state.abMode) {
      const payloadB = buildGeneratePayload(); // 若有B，第二次再发
      await triggerGeneration(payloadB);
    }
  } finally {
    setBusy(false);
  }
}

function resolveDocumentAssetBase() {
  if (documentAssetBase) return documentAssetBase;
  const baseEl = document.querySelector('base[href]');
  if (baseEl) {
    documentAssetBase = baseEl.href;
    return documentAssetBase;
  }
  const { origin, pathname } = window.location;
  const parts = pathname.split('/');
  if (parts.length) parts.pop();
  const prefix = parts.join('/') || '/';
  documentAssetBase = `${origin}${prefix.endsWith('/') ? prefix : `${prefix}/`}`;
  return documentAssetBase;
}

function assetUrl(path) {
  if (!path) return resolveDocumentAssetBase();
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(path)) {
    return path;
  }
  const base = resolveDocumentAssetBase();
  const normalised = path.startsWith('/') ? path.slice(1) : path;
  return new URL(normalised, base).toString();
}

App.utils.assetUrl = assetUrl;

// Layout helpers for relative-coordinates templates
App.utils.resolveRect = function resolveRect(slot, canvasWidth, canvasHeight, parentRect) {
  if (!slot) return { x: 0, y: 0, w: 0, h: 0 };
  const px = parentRect ? parentRect.x : 0;
  const py = parentRect ? parentRect.y : 0;
  const pw = parentRect ? parentRect.w : canvasWidth;
  const ph = parentRect ? parentRect.h : canvasHeight;

  return {
    x: px + Number(slot.x || 0) * pw,
    y: py + Number(slot.y || 0) * ph,
    w: Number(slot.w || 0) * pw,
    h: Number(slot.h || 0) * ph,
  };
};

App.utils.fontPx = function fontPx(font, canvasHeight) {
  if (!font) return 0;
  const size = typeof font.size === 'number' ? font.size : 0.02;
  return size * canvasHeight;
};

function normaliseBase(base) {
  if (!base) return null;
  try {
    const parsed = new URL(base, window.location.href);
    const path = parsed.pathname.replace(/\/+$/, '');
    const normalizedPath = path || '';
    return `${parsed.origin}${normalizedPath}`;
  } catch (error) {
    console.warn('[normaliseBase] invalid base', base, error);
    return null;
  }
}
// 把 stage1Data 中的素材“二选一”规范化为 key 或小 dataURL
function normalizePosterAssets(stage1Data) {
  const pickImage = (asset) => {
    if (!asset) return { asset: null, key: null };
    const key = asset.r2Key || null;
    const data = typeof asset.dataUrl === 'string' && asset.dataUrl.startsWith('data:')
      ? asset.dataUrl
      : null;
    return key ? { asset: null, key } : { asset: data, key: null };
  };

  const { asset: scenario_asset, key: scenario_key } = pickImage(stage1Data.scenario_asset);
  const { asset: product_asset,  key: product_key  } = pickImage(stage1Data.product_asset);

  const gallery_items = (stage1Data.gallery_entries || []).map((entry) => {
    const { asset, key } = pickImage(entry.asset);
    const mode = entry.mode || 'upload';
    const normalisedMode = mode === 'logo' || mode === 'logo_fallback' ? 'upload' : mode;
    return {
      caption: entry.caption?.trim() || null,
      asset,
      key,
      mode: normalisedMode,
      prompt: entry.prompt?.trim() || null,
    };
  });

  return { scenario_asset, scenario_key, product_asset, product_key, gallery_items };
}

function joinBasePath(base, path) {
  const normalised = normaliseBase(base);
  if (!normalised) return null;
  const p = String(path || '');
  const suffix = p.startsWith('/') ? p : `/${p}`;
  return `${normalised}${suffix}`;
}

function ensureArray(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}



// 读取候选 API 基址（修复：避免 STORAGE_KEYS 的 TDZ）
function getApiCandidates(extra) {
  const candidates = new Set();
  const add = (v) => {
    const s = typeof v === 'string' ? v.trim() : '';
    if (!s) return;
    const n = normaliseBase(s);
    if (n) candidates.add(n);
  };

  const inputValue = document.getElementById('api-base')?.value;
  add(inputValue);

  // 避免对未初始化的 STORAGE_KEYS 访问；直接用字面量 key
  add(localStorage.getItem('marketing-poster-api-base'));

  const ds = document.body?.dataset ?? {};
  add(ds.workerBase);
  add(ds.renderBase);
  add(ds.apiBase);

  if (Array.isArray(window.APP_API_BASES)) window.APP_API_BASES.forEach(add);
  add(window.APP_WORKER_BASE);
  add(window.APP_RENDER_BASE);
  add(window.APP_DEFAULT_API_BASE);

  if (extra) ensureArray(extra).forEach(add);

  return Array.from(candidates);
}

App.utils.getApiCandidates = getApiCandidates;

async function probeBase(base, { force } = {}) {
  const now = Date.now();
  const cached = HEALTH_CACHE.get(base);
  if (!force && cached && now - cached.timestamp < HEALTH_CACHE_TTL) {
    return cached.ok;
  }

  const paths = healthPathsFor(base);           // ← 关键：按域名取路径
  for (const path of paths) {
    const url = joinBasePath(base, path);
    if (!url) continue;
    try {
      const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-store',
        credentials: 'omit',
      });
      if (response.ok) {
        HEALTH_CACHE.set(base, { ok: true, timestamp: Date.now() });
        return true;
      }
    } catch (error) {
      console.warn('[probeBase] failed', base, path, error);
    }
  }

  HEALTH_CACHE.set(base, { ok: false, timestamp: Date.now() });
  return false;
}


const warmUpLocks = new Map();

async function warmUp(baseOrBases, { force } = {}) {
  const bases = ensureArray(baseOrBases).filter(Boolean);
  const targets = bases.length ? bases : getApiCandidates();
  if (!targets.length) return [];

  const lockKey = [...targets].sort().join('|');
  const existing = warmUpLocks.get(lockKey);
  if (!force && existing) return existing;

  const task = Promise.allSettled(targets.map((base) => probeBase(base, { force })));
  warmUpLocks.set(lockKey, task);
  // 任务结束后释放锁
  task.finally(() => warmUpLocks.delete(lockKey));
  return task;
}

App.utils.warmUp = warmUp;

async function pickHealthyBase(baseOrBases) {
  const candidates = ensureArray(baseOrBases).filter(Boolean);
  const bases = candidates.length ? candidates : getApiCandidates();
  if (!bases.length) return null;

  const now = Date.now();
  for (const base of bases) {
    const cached = HEALTH_CACHE.get(base);
    if (cached && cached.ok && now - cached.timestamp < HEALTH_CACHE_TTL) {
      return base;
    }
  }

  const results = await warmUp(bases, { force: true });
  for (let i = 0; i < bases.length; i += 1) {
    const outcome = results[i];
    if (outcome && outcome.status === 'fulfilled' && outcome.value) {
      return bases[i];
    }
  }
  return null;
}

App.utils.pickHealthyBase = pickHealthyBase;

// 请求体大小校验（发送前统一做）
// 校验字符串体积并阻断超大 dataURL
function validatePayloadSize(raw) {
  const hasBase64 = /data:[^;]+;base64,/i.test(raw);
  // 300KB 是你当前防御阈值，可按需调整
  if (hasBase64 || raw.length > 300_000) {
    throw new Error('请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url。');
  }
}

const DATA_URL_PAYLOAD_RX = /^data:image\/[a-z0-9.+-]+;base64,/i;
const HTTP_URL_RX = /^https?:\/\//i;
const URL_SCHEMES = ['http://', 'https://', 'r2://', 's3://', 'gs://'];

const DEFAULT_ASSET_BUCKET =
  window.__ASSET_BUCKET__ || window.__R2_BUCKET__ || window.__S3_BUCKET__ || 'poster-assets';
const DEFAULT_ASSET_SCHEME =
  window.__ASSET_SCHEME__ || (window.__S3_BUCKET__ ? 's3' : 'r2');
const PUBLIC_ASSET_BASE =
  window.__ASSET_PUBLIC_BASE__ || window.__R2_PUBLIC_BASE__ || window.__S3_PUBLIC_BASE__ || '';

function isUrlLike(value) {
  if (typeof value !== 'string') return false;
  const trimmed = value.trim();
  if (!trimmed) return false;
  return URL_SCHEMES.some((scheme) => trimmed.startsWith(scheme));
}

function toAssetUrl(input) {
  if (!input) return '';
  const trimmed = input.trim();
  if (!trimmed) return '';
  if (isUrlLike(trimmed)) return trimmed;
  const sanitised = trimmed.replace(/^\/+/, '');
  if (PUBLIC_ASSET_BASE) {
    const base = PUBLIC_ASSET_BASE.replace(/\/$/, '');
    return `${base}/${sanitised}`;
  }
  if (DEFAULT_ASSET_BUCKET && DEFAULT_ASSET_SCHEME) {
    return `${DEFAULT_ASSET_SCHEME}://${DEFAULT_ASSET_BUCKET.replace(/\/$/, '')}/${sanitised}`;
  }
  return sanitised;
}

function assertAssetUrl(fieldLabel, value) {
  if (!value || !isUrlLike(value)) {
    throw new Error(`${fieldLabel} 必须是 r2://、s3://、gs:// 或 http(s) 的 URL，请先上传到 R2，仅传 Key/URL`);
  }
}

function guessExtensionFromMime(mime) {
  if (!mime) return 'png';
  const normalised = mime.toLowerCase();
  if (normalised.includes('png')) return 'png';
  if (normalised.includes('jpeg') || normalised.includes('jpg')) return 'jpg';
  if (normalised.includes('webp')) return 'webp';
  if (normalised.includes('gif')) return 'gif';
  return 'png';
}

async function dataUrlToFile(dataUrl, nameHint = 'asset') {
  const response = await fetch(dataUrl);
  if (!response.ok) {
    throw new Error('无法解析内联图片，请重新上传素材。');
  }
  const blob = await response.blob();
  const mime = blob.type || inferImageMediaType(dataUrl) || 'image/png';
  const extension = guessExtensionFromMime(mime);
  const safeHint = nameHint.toString().trim().replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '') || 'asset';
  const filename = `${safeHint}.${extension}`;
  const file = new File([blob], filename, { type: mime });
  return { file, mime, extension, filename };
}

function estimatePayloadBytes(data) {
  try {
    if (typeof data === 'string') {
      return new Blob([data]).size;
    }
    return new Blob([JSON.stringify(data)]).size;
  } catch (error) {
    console.warn('[client] unable to estimate payload size', error);
    return -1;
  }
}

function payloadContainsDataUrl(value) {
  if (typeof value === 'string') return DATA_URL_PAYLOAD_RX.test(value);
  if (Array.isArray(value)) return value.some(payloadContainsDataUrl);
  if (value && typeof value === 'object') {
    return Object.values(value).some(payloadContainsDataUrl);
  }
  return false;
}

async function normaliseAssetReference(
  asset,
  {
    field = 'asset',
    required = true,
    // backward compatibility: honour legacy requireUploaded if provided
    requireUploaded = undefined,
    apiCandidates = [],
    folder = 'uploads',
  } = {},
  brandLogo = null,
) {
  const mustHaveUpload =
    typeof required === 'boolean'
      ? required
      : typeof requireUploaded === 'boolean'
        ? requireUploaded
        : true;
  const candidates = Array.isArray(apiCandidates) ? apiCandidates.filter(Boolean) : [];

  const ensureUploaderAvailable = () => {
    if (!candidates.length) {
      throw new Error(`${field} 检测到 base64 图片，请先上传到 R2/GCS，仅传 key/url`);
    }
  };

  const ensureNotInline = (value) => {
    if (typeof value !== 'string') return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    if (DATA_URL_PAYLOAD_RX.test(trimmed)) {
      return null;
    }
    return trimmed;
  };

  const normaliseKey = (value) => {
    const trimmed = ensureNotInline(value);
    if (!trimmed) return null;
    return trimmed.replace(/^\/+/, '');
  };

  const uploadInlineAsset = async (dataUrl) => {
    if (!dataUrl || !DATA_URL_PAYLOAD_RX.test(dataUrl)) return null;
    ensureUploaderAvailable();
    const safeHint = field.replace(/[^a-z0-9]+/gi, '_') || 'asset';
    const { file } = await dataUrlToFile(dataUrl, safeHint);
    const result = await uploadFileToR2(folder, file, { bases: candidates });
    if (!result.uploaded || (!result.url && !result.key)) {
      throw new Error(`${field} 上传失败，请稍后重试。`);
    }
    const finalUrl = result.url || toAssetUrl(result.key);
    if (!finalUrl || !isUrlLike(finalUrl)) {
      throw new Error(`${field} 上传失败，无法解析生成的 URL。`);
    }
    return {
      key: result.key ? result.key.replace(/^\/+/, '') : null,
      url: finalUrl,
    };
  };

  // Handle explicit logo fallback: coerce to upload with brand logo reference
  if (asset && typeof asset === 'object' && asset.mode === 'logo') {
    const logoKey = brandLogo?.key || brandLogo?.r2Key || null;
    const logoUrl = brandLogo?.url || brandLogo?.remoteUrl || brandLogo?.cdnUrl || null;
    if (!logoKey && !logoUrl) {
      throw new Error(`${field} 使用 logo 兜底失败: 品牌 Logo 缺少 URL/Key`);
    }
    asset = { ...asset, key: logoKey || asset.key || null, url: logoUrl || asset.url || null, mode: 'upload' };
  }

  if (!asset) {
    if (mustHaveUpload) {
      throw new Error(`${field} 缺少已上传的 URL/Key，请先完成素材上传。`);
    }
    return { key: null, url: null };
  }

  if (typeof asset === 'string') {
    const trimmed = asset.trim();
    if (!trimmed) {
      if (mustHaveUpload) {
        throw new Error(`${field} 缺少已上传的 URL/Key，请先完成素材上传。`);
      }
      return { key: null, url: null };
    }
    if (DATA_URL_PAYLOAD_RX.test(trimmed)) {
      const uploaded = await uploadInlineAsset(trimmed);
      if (uploaded) {
        return uploaded;
      }
    }
    const resolved = toAssetUrl(trimmed);
    if (!isUrlLike(resolved)) {
      if (mustHaveUpload) {
        throw new Error(`${field} 必须是 r2://、s3://、gs:// 或 http(s) 的 URL，请先上传到 R2，仅传 Key/URL`);
      }
    }
    return { key: HTTP_URL_RX.test(trimmed) ? null : trimmed.replace(/^\/+/, ''), url: isUrlLike(resolved) ? resolved : null };
  }

  let keyCandidate = normaliseKey(asset.r2Key || asset.key || asset.storage_key || null);
  let resolvedUrl = null;
  let inlineCandidate = null;

  const sourceCandidates = [asset.remoteUrl, asset.url, asset.publicUrl, asset.cdnUrl, asset.dataUrl];
  for (const candidate of sourceCandidates) {
    if (typeof candidate !== 'string') continue;
    const trimmed = candidate.trim();
    if (!trimmed) continue;
    if (DATA_URL_PAYLOAD_RX.test(trimmed)) {
      inlineCandidate = inlineCandidate || trimmed;
      continue;
    }
    if (isUrlLike(trimmed)) {
      resolvedUrl = toAssetUrl(trimmed);
      break;
    }
    if (!HTTP_URL_RX.test(trimmed) && !keyCandidate) {
      keyCandidate = normaliseKey(trimmed) || keyCandidate;
    }
  }

  if (!resolvedUrl && inlineCandidate) {
    const uploaded = await uploadInlineAsset(inlineCandidate);
    if (uploaded) {
      resolvedUrl = uploaded.url;
      keyCandidate = uploaded.key || keyCandidate;
      if (typeof asset === 'object') {
        asset.r2Key = uploaded.key || asset.r2Key || null;
        asset.remoteUrl = uploaded.url;
        asset.dataUrl = uploaded.url;
      }
      console.info(`[normaliseAssetReference] 已将 ${field} 的 base64 预览上传至 R2/GCS。`);
    }
  }

  if (!resolvedUrl && keyCandidate) {
    const derivedUrl = toAssetUrl(keyCandidate);
    if (isUrlLike(derivedUrl)) {
      resolvedUrl = derivedUrl;
    }
  }

  if (!resolvedUrl) {
    if (mustHaveUpload) {
      throw new Error(`${field} 缺少已上传的 URL/Key，请先完成素材上传。`);
    }
    return { key: keyCandidate || null, url: null };
  }

  if (!isUrlLike(resolvedUrl)) {
    if (mustHaveUpload) {
      throw new Error(`${field} 必须是 r2://、s3://、gs:// 或 http(s) 的 URL，请先上传到 R2，仅传 Key/URL`);
    }
    return { key: keyCandidate || null, url: null };
  }

  return {
    key: keyCandidate ? keyCandidate.replace(/^\/+/, '') : null,
    url: resolvedUrl,
  };
}

function summariseNegativePrompts(prompts) {
  if (!prompts || typeof prompts !== 'object') return null;
  const values = [];
  Object.values(prompts).forEach((entry) => {
    if (!entry) return;
    const negative = typeof entry.negative === 'string' ? entry.negative.trim() : '';
    if (negative) values.push(negative);
  });
  if (!values.length) return null;
  return Array.from(new Set(values)).join(' | ');
}

function ensureUploadedAndLog(path, payload, rawPayload) {
  const MAX = 512 * 1024;
  const requestId = (typeof crypto !== 'undefined' && crypto.randomUUID)
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(16).slice(2, 10);
  let bodyString = null;
  if (typeof rawPayload === 'string') {
    bodyString = rawPayload;
  } else if (payload !== undefined) {
    try {
      bodyString = JSON.stringify(payload);
    } catch (error) {
      console.warn('[client] stringify payload failed', error);
    }
  }

  const size = estimatePayloadBytes(bodyString ?? payload);
  const hasBase64 = payloadContainsDataUrl(bodyString ?? payload);
  const preview = typeof bodyString === 'string'
    ? (bodyString.length > 512 ? `${bodyString.slice(0, 512)}…(+${bodyString.length - 512} chars)` : bodyString)
    : null;

  console.log(`[client] pre-check ${path}`, {
    requestId,
    size,
    hasBase64,
    preview,
  });

  if (hasBase64) {
    throw new Error('检测到 base64 图片，请先上传到 R2/GCS，仅传 key/url');
  }
  if (MAX > 0 && size > MAX) {
    throw new Error(`请求体过大(${size}B)，请仅传 key/url`);
  }

  return {
    headers: { 'X-Request-ID': requestId },
    bodyString,
    size,
  };
}

// 完整替换 app.js 里的 postJsonWithRetry
// 发送请求：始终 JSON/UTF-8，支持多基址与重试
// 发送请求：始终 JSON/UTF-8，支持多基址与重试
async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
  // 1) 规范化候选基址
  const bases = (window.resolveApiBases?.(apiBaseOrBases))
    ?? (Array.isArray(apiBaseOrBases) ? apiBaseOrBases
        : String(apiBaseOrBases || '').split(',').map(s => s.trim()).filter(Boolean));
  if (!bases.length) throw new Error('未配置后端 API 地址');

  const inspection = ensureUploadedAndLog(path, payload, rawPayload);

  // 2) 组包（外部已给字符串就不再二次 JSON.stringify）
  const bodyRaw = (typeof rawPayload === 'string')
    ? rawPayload
    : inspection.bodyString ?? JSON.stringify(payload);

  const logPrefix = `[postJsonWithRetry] ${path}`;
  const previewSnippet = (() => {
    if (typeof bodyRaw !== 'string') return '';
    const limit = 512;
    return bodyRaw.length <= limit ? bodyRaw : `${bodyRaw.slice(0, limit)}…(+${bodyRaw.length - limit} chars)`;
  })();

  // 3) 粗略体积 & dataURL 防御
  if (typeof bodyRaw === 'string' && (/data:[^;]+;base64,/.test(bodyRaw) || bodyRaw.length > 300000)) {
    throw new Error('请求体过大或包含 base64 图片，请确保素材已直传并仅传 key/url。');
  }

  // 4) 选择健康基址
  let base = await (window.pickHealthyBase?.(bases, { timeoutMs: 2500 })) ?? bases[0];
  const urlFor = (b) => `${String(b).replace(/\/$/, '')}/${String(path).replace(/^\/+/, '')}`;
  let lastErr = null;

  for (let attempt = 0; attempt <= retry; attempt += 1) {
    const order = base ? [base, ...bases.filter(x => x !== base)] : bases;

    for (const b of order) {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 60000); // 60s 超时
      const url = urlFor(b);                               // ← 定义 url
      try {
        const headers = {
          'Content-Type': 'application/json; charset=UTF-8',
          ...(inspection?.headers || {}),
        };

        const res = await fetch(url, {
          method: 'POST',
          mode: 'cors',
          cache: 'no-store',
          credentials: 'omit',
          headers,
          body: bodyRaw,
          signal: ctrl.signal,
        });

        console.info(`${logPrefix} -> ${url}`, {
          attempt: attempt + 1,
          candidateIndex: order.indexOf(b),
          bodyBytes: typeof bodyRaw === 'string' ? bodyRaw.length : 0,
          status: res.status,
        });

        const text = await res.text();
        let json = null;
        try { json = text ? JSON.parse(text) : null; } catch { /* 非 JSON */ }

        if (!res.ok) {
          const detail = (json && (json.detail || json.message)) || text || `HTTP ${res.status}`;
          const error = new Error(detail);
          error.status = res.status;
          error.responseText = text;
          error.responseJson = json;
          error.url = url;
          error.requestBody = bodyRaw;
          throw error;
        }

        if (window._healthCache?.set) window._healthCache.set(b, { ok: true, ts: Date.now() });
        return json ?? {}; // 保持旧版语义：返回 JSON 对象
      } catch (e) {
        console.warn(`${logPrefix} failed`, {
          attempt: attempt + 1,
          url,
          message: e?.message,
          status: e?.status,
          bodyPreview: previewSnippet,
        });
        lastErr = e;
        if (window._healthCache?.set) window._healthCache.set(b, { ok: false, ts: Date.now() });
        base = null; // 该轮失败，下一轮重新挑
      } finally {
        clearTimeout(timer);
      }
    }

    // 整轮失败后：热身 + 等待 + 重选
    try { await window.warmUp?.(bases, { timeoutMs: 2500 }); } catch {}
    await new Promise(r => setTimeout(r, 800));
    base = await (window.pickHealthyBase?.(bases, { timeoutMs: 2500 })) ?? bases[0];
  }

  throw lastErr || new Error('请求失败');
}

App.utils.postJsonWithRetry = postJsonWithRetry;


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

const placeholderImages = {
  brandLogo: createPlaceholder('品牌\\nLogo'),
  scenario: createPlaceholder('应用场景'),
  product: createPlaceholder('产品渲染'),
};

const galleryPlaceholderCache = new Map();

const MATERIAL_DEFAULT_LABELS = {
  brand_logo: '品牌 Logo',
  scenario: '应用场景图',
  product: '主产品渲染图',
  gallery: '底部产品小图',
};

const assetStore = createAssetStore();

function getPosterImageSource(image) {
  if (!image || typeof image !== 'object') return '';
  const directUrl = typeof image.url === 'string' ? image.url.trim() : '';
  if (directUrl && (HTTP_URL_RX.test(directUrl) || directUrl.startsWith('data:'))) {
    return directUrl;
  }
  const dataUrl = typeof image.data_url === 'string' ? image.data_url.trim() : '';
  if (dataUrl && dataUrl.startsWith('data:')) {
    return dataUrl;
  }
  return '';
}

function inferImageMediaType(src) {
  if (typeof src !== 'string') return null;
  const value = src.split('?')[0].trim().toLowerCase();
  if (!value) return null;
  if (value.startsWith('data:image/')) {
    const match = value.match(/^data:(image\/[a-z0-9.+-]+);/);
    return match ? match[1] : null;
  }
  if (value.endsWith('.png')) return 'image/png';
  if (value.endsWith('.jpg') || value.endsWith('.jpeg')) return 'image/jpeg';
  if (value.endsWith('.webp')) return 'image/webp';
  if (value.endsWith('.gif')) return 'image/gif';
  return null;
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

function isSamePosterImage(a, b) {
  if (!a || !b) return false;
  if (a === b) return true;
  const filenameA = typeof a.filename === 'string' ? a.filename : '';
  const filenameB = typeof b.filename === 'string' ? b.filename : '';
  if (filenameA && filenameB && filenameA === filenameB) {
    return true;
  }
  const urlA = getPosterImageSource(a);
  const urlB = getPosterImageSource(b);
  if (urlA && urlB && urlA === urlB) {
    return true;
  }
  const dataA = typeof a.data_url === 'string' ? a.data_url : '';
  const dataB = typeof b.data_url === 'string' ? b.data_url : '';
  if (dataA && dataB && dataA === dataB) {
    return true;
  }
  const keyA = typeof a.storage_key === 'string' ? a.storage_key : '';
  const keyB = typeof b.storage_key === 'string' ? b.storage_key : '';
  return Boolean(keyA && keyB && keyA === keyB);
}

// 预签名上传：向后端申请 R2 PUT 地址，并可直接完成上传
// 返回 { key, put_url, get_url, r2_url, public_url, etag, content_type, size }
async function r2PresignPut(folder, file, bases, options = {}) {
  if (!file) throw new Error('没有可上传的文件');

  const retry = options.retry ?? 1;
  const contentType = file.type || 'image/png'; // 图片默认 image/png 更稳
  const size = (typeof file.size === 'number') ? file.size : null;

  // 1) 申请预签名
  const payload = {
    folder: folder || 'uploads',
    filename: file.name || 'upload.bin',
    content_type: contentType,
    size,
  };
  const resp = await postJsonWithRetry(bases, '/api/r2/presign-put', payload, retry);
  const data = (resp && typeof resp.json === 'function') ? await resp.json() : resp;

  if (!data || typeof data !== 'object') throw new Error('预签名接口返回异常');
  const {
    key,
    put_url: putUrl,
    get_url: getUrl,
    r2_url: r2Url,
    public_url: legacyPublicUrl,
  } = data;
  if (!key || !putUrl) throw new Error('预签名接口缺少 key 或 put_url');
  const normalizedR2 = r2Url || null;
  const readableUrl = getUrl || legacyPublicUrl || null;

  // 2) 直接上传到 R2（options.upload === false 可只要签名不上传）
  if (options.upload !== false) {
    const putRes = await fetch(putUrl, {
      method: 'PUT',
      headers: { 'Content-Type': contentType }, // 关键：写入正确 Content-Type
      body: file,
    });
    if (!putRes.ok) {
      const txt = await putRes.text().catch(() => '');
      throw new Error(`R2 上传失败：HTTP ${putRes.status} ${putRes.statusText} ${txt || ''}`.trim());
    }
    const etag = putRes.headers.get('etag') || null;
    return {
      key,
      put_url: putUrl,
      get_url: readableUrl,
      r2_url: normalizedR2,
      public_url: readableUrl,
      etag,
      content_type: contentType,
      size,
    };
  }

  // 仅返回签名信息
  return {
    key,
    put_url: putUrl,
    get_url: readableUrl,
    r2_url: normalizedR2,
    public_url: readableUrl,
    content_type: contentType,
    size,
  };
}


async function uploadFileToR2(folder, file, options = {}) {
  try {
    const shouldUpload = options?.upload !== false;
    const presign = await r2PresignPut(folder, file, options?.bases, {
      upload: false,
    });
    if (shouldUpload) {
      const headers = (presign.headers && Object.keys(presign.headers).length)
        ? presign.headers
        : { 'Content-Type': file?.type || 'application/octet-stream' };

      const putResponse = await fetch(presign.put_url, {
        method: 'PUT',
        headers,
        body: file,
        mode: 'cors',
      });
      if (!putResponse.ok) {
        const detail = await putResponse.text();
        throw new Error(detail || '上传到 R2 失败，请稍后重试。');
      }
    }
    const selectHttpUrl = (value) => {
      if (typeof value !== 'string') return null;
      const trimmed = value.trim();
      if (!trimmed) return null;
      return HTTP_URL_RX.test(trimmed) ? trimmed : null;
    };
    const accessibleUrl =
      selectHttpUrl(presign.get_url) || selectHttpUrl(presign.public_url);
    const derivedUrl = selectHttpUrl(toAssetUrl(presign.key));
    const referenceUrl = accessibleUrl || derivedUrl || null;
    return {
      key: presign.key,
      url: referenceUrl,
      uploaded: true,
      presign,
    };
  } catch (error) {
    console.error('[uploadFileToR2] 直传失败', error);
    if (error instanceof TypeError) {
      const origin = (typeof window !== 'undefined' && window.location)
        ? window.location.origin
        : '当前站点';
      const message = `R2 上传失败：请确认对象存储的 CORS 规则已允许 ${origin} 执行 PUT 请求。`;
      const corsError = new Error(message);
      corsError.code = 'R2_CORS_BLOCKED';
      throw corsError;
    }
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('上传到 R2 失败，请稍后重试。');
  }
}

App.utils.r2PresignPut = r2PresignPut;
App.utils.uploadFileToR2 = uploadFileToR2;
App.utils.updateMaterialUrlDisplay = updateMaterialUrlDisplay;

function applyStoredAssetValue(target, storedValue) {
  if (!target || typeof storedValue !== 'string') return;
  if (storedValue.startsWith('data:')) {
    target.data_url = storedValue;
  } else {
    target.url = storedValue;
  }
}

function updateMaterialUrlDisplay(field, asset) {
  const container = document.querySelector(`[data-material-url="${field}"]`);
  if (!container) return;

  const label = container.dataset.label || '素材 URL：';
  const prefix = label.endsWith('：') ? label : `${label}：`;
  const urlCandidates = [];
  if (asset) {
    if (typeof asset === 'string') {
      if (HTTP_URL_RX.test(asset)) urlCandidates.push(asset);
    } else if (typeof asset === 'object') {
      const {
        remoteUrl,
        url,
        publicUrl,
        dataUrl,
      } = asset;
      [remoteUrl, url, publicUrl].forEach((candidate) => {
        if (typeof candidate === 'string' && HTTP_URL_RX.test(candidate)) {
          urlCandidates.push(candidate);
        }
      });
      if (typeof dataUrl === 'string' && HTTP_URL_RX.test(dataUrl)) {
        urlCandidates.push(dataUrl);
      }
    }
  }

  const url = urlCandidates.find(Boolean) || null;
  container.textContent = '';
  const labelSpan = document.createElement('span');
  labelSpan.classList.add('asset-url-label');
  labelSpan.textContent = prefix;
  container.appendChild(labelSpan);

  if (url) {
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = url;
    container.appendChild(link);
    container.classList.add('has-url');
  } else {
    const placeholder = document.createElement('span');
    placeholder.classList.add('asset-url-empty');
    placeholder.textContent = '尚未上传';
    container.appendChild(placeholder);
    container.classList.remove('has-url');
  }
}

// ==== 兜底：保持原命名的 loadTemplateRegistry（放在 init() 之前）====
(function ensureLoadTemplateRegistry() {
  const REG_PATH = (typeof TEMPLATE_REGISTRY_PATH === 'string' && TEMPLATE_REGISTRY_PATH)
    ? TEMPLATE_REGISTRY_PATH
    : 'templates/registry.json';

  if (typeof window.loadTemplateRegistry !== 'function') {
    let _tmplRegistryPromise = null;
    window.loadTemplateRegistry = async function loadTemplateRegistry() {
      if (!_tmplRegistryPromise) {
        _tmplRegistryPromise = fetch(assetUrl(REG_PATH))
          .then((r) => {
            if (!r.ok) throw new Error('无法加载模板清单');
            return r.json();
          })
          .then((arr) => (Array.isArray(arr) ? arr : []))
          .catch((err) => {
            _tmplRegistryPromise = null; // 失败允许下次重试
            throw err;
          });
      }
      return _tmplRegistryPromise;
    };
  }
})();

function init() {
  apiBaseInput = document.getElementById('api-base');
  loadApiBase();
  if (apiBaseInput) {
    apiBaseInput.addEventListener('change', saveApiBase);
    apiBaseInput.addEventListener('blur', saveApiBase);
  }

  const stage = document.body?.dataset?.stage;
  switch (stage) {
    case 'stage1':
      initStage1();
      break;
    case 'stage2':
      initStage2();
      break;
    case 'stage3':
      initStage3();
      break;
    default:
      break;
  }
}

document.addEventListener('DOMContentLoaded', init);

function loadApiBase() {
  if (!apiBaseInput) return;
  const stored = localStorage.getItem(STORAGE_KEYS.apiBase);
  if (stored) {
    apiBaseInput.value = stored;
  }
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

function initStage1() {
  const form = document.getElementById('poster-form');
  const buildPreviewButton = document.getElementById('build-preview');
  const nextButton = document.getElementById('go-to-stage2');
  const statusElement = document.getElementById('stage1-status');
  const previewContainer = document.getElementById('preview-container');
  const layoutStructure = document.getElementById('layout-structure-text');
  const galleryButton = document.getElementById('add-gallery-item');
  const galleryPlaceholderButton = document.getElementById('add-gallery-placeholder');
  const galleryFileInput = document.getElementById('gallery-file-input');
  const galleryItemsContainer = document.getElementById('gallery-items');
  const templateSelectStage1 = document.getElementById('template-select-stage1');
  const templateDescriptionStage1 = document.getElementById('template-description-stage1');
  const templateCanvasStage1 = document.getElementById('template-preview-stage1');
  

  if (!form || !buildPreviewButton || !nextButton) {
    return;
  }

  const previewElements = {
    brandLogo: document.getElementById('preview-brand-logo'),
    brandName: document.getElementById('preview-brand-name'),
    agentName: document.getElementById('preview-agent-name'),
    scenarioImage: document.getElementById('preview-scenario-image'),
    productImage: document.getElementById('preview-product-image'),
    featureList: document.getElementById('preview-feature-list'),
    title: document.getElementById('preview-title'),
    subtitle: document.getElementById('preview-subtitle'),
    gallery: document.getElementById('preview-gallery'),
  };

  const inlinePreviews = {
    brand_logo: document.querySelector('[data-inline-preview="brand_logo"]'),
    scenario_asset: document.querySelector('[data-inline-preview="scenario_asset"]'),
    product_asset: document.querySelector('[data-inline-preview="product_asset"]'),
  };

  const state = {
    brandLogo: null,
    scenario: null,
    product: null,
    galleryEntries: [],
    previewBuilt: false,
    templateId: DEFAULT_STAGE1.template_id,
    templateLabel: '',
    scenarioMode: DEFAULT_STAGE1.scenario_mode,
    productMode: DEFAULT_STAGE1.product_mode,
    scenarioType: 'image',
    scenarioAllowsPrompt: true,
    scenarioAllowsUpload: true,
    productType: 'image',
    productAllowsPrompt: true,
    productAllowsUpload: true,
    templateSpec: null,
    galleryLimit: 4,
    galleryAllowsPrompt: true,
    galleryAllowsUpload: true,
    galleryLabel: MATERIAL_DEFAULT_LABELS.gallery,
    galleryType: 'image',
  };

  updateMaterialUrlDisplay('brand_logo', state.brandLogo);

  let currentLayoutPreview = '';
  let templateRegistry = [];

  const refreshPreview = () => {
    if (!form) return null;
    const payload = collectStage1Data(form, state, { strict: false });
    currentLayoutPreview = updatePosterPreview(
      payload,
      state,
      previewElements,
      layoutStructure,
      previewContainer
    );
    return payload;
  };

  const stored = loadStage1Data();
  if (stored) {
    void (async () => {
      await applyStage1DataToForm(stored, form, state, inlinePreviews);
      state.previewBuilt = Boolean(stored.preview_built);
      currentLayoutPreview = stored.layout_preview || '';
      renderGalleryItems(state, galleryItemsContainer, {
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement,
        form,
        inlinePreviews,
        onChange: refreshPreview,
        allowPrompt: state.galleryAllowsPrompt,
        forcePromptOnly: state.galleryAllowsUpload === false,
        promptPlaceholder:
          state.templateSpec?.materials?.gallery?.promptPlaceholder ||
          '描述要生成的小图内容',
      });
      refreshPreview();
    })();
  } else {
    applyStage1Defaults(form);
    updateInlinePlaceholders(inlinePreviews);
    applyModeToInputs('scenario', state, form, inlinePreviews, { initial: true });
    applyModeToInputs('product', state, form, inlinePreviews, { initial: true });
    refreshPreview();
  }

  const modeContext = { form, state, inlinePreviews, refreshPreview };

  const scenarioModeRadios = form.querySelectorAll('input[name="scenario_mode"]');
  scenarioModeRadios.forEach((radio) => {
    radio.addEventListener('change', (event) => {
      if (!radio.checked) return;
      const value = radio.value === 'prompt' ? 'prompt' : 'upload';
      void switchAssetMode('scenario', value, modeContext);
    });
  });

  const productModeRadios = form.querySelectorAll('input[name="product_mode"]');
  productModeRadios.forEach((radio) => {
    radio.addEventListener('change', (event) => {
      if (!radio.checked) return;
      const value = radio.value === 'prompt' ? 'prompt' : 'upload';
      void switchAssetMode('product', value, modeContext);
    });
  });

  const getMaterialLabel = (key, material) =>
    (material && typeof material.label === 'string' && material.label.trim()) ||
    MATERIAL_DEFAULT_LABELS[key] || key;

  async function applyTemplateMaterialsStage1(spec) {
    state.templateSpec = spec || null;
    const materials = (spec && spec.materials) || {};

    const brandMaterial = materials.brand_logo || {};
    const brandLabel = getMaterialLabel('brand_logo', brandMaterial);
    const brandField = form.querySelector('[data-material-field="brand_logo"] [data-material-label="brand_logo"]');
    if (brandField) {
      brandField.textContent = `${brandLabel}上传`;
    }

    const scenarioMaterial = materials.scenario || {};
    const scenarioLabel = getMaterialLabel('scenario', scenarioMaterial);
    const scenarioType = (scenarioMaterial.type || 'image').toLowerCase();
    const scenarioAllowsUpload = scenarioType !== 'text' && scenarioMaterial.allowsUpload !== false;
    const scenarioAllowsPrompt =
      scenarioType === 'text' || scenarioMaterial.allowsPrompt !== false;
    state.scenarioType = scenarioType;
    state.scenarioAllowsPrompt = scenarioAllowsPrompt;
    state.scenarioAllowsUpload = scenarioAllowsUpload;

    const scenarioToggleLabel = form.querySelector('[data-material-toggle-label="scenario"]');
    if (scenarioToggleLabel) {
      scenarioToggleLabel.textContent = `${scenarioLabel}素材来源`;
    }
    const scenarioToggle = form.querySelector('[data-mode-target="scenario"]');
    const scenarioUploadOption = form.querySelector('[data-mode-option="scenario-upload"]');
    const scenarioUploadRadio = scenarioUploadOption?.querySelector('input[type="radio"]');
    if (scenarioUploadOption) {
      scenarioUploadOption.classList.toggle('hidden', !scenarioAllowsUpload);
    }
    if (scenarioUploadRadio) {
      scenarioUploadRadio.disabled = !scenarioAllowsUpload;
    }
    const scenarioPromptOption = form.querySelector('[data-mode-option="scenario-prompt"]');
    const scenarioPromptRadio = scenarioPromptOption?.querySelector('input[type="radio"]');
    if (scenarioPromptOption) {
      scenarioPromptOption.classList.toggle('hidden', !scenarioAllowsPrompt);
    }
    if (scenarioPromptRadio) {
      scenarioPromptRadio.disabled = !scenarioAllowsPrompt;
    }
    if (scenarioToggle) {
      scenarioToggle.classList.toggle(
        'single-mode',
        !scenarioAllowsUpload || !scenarioAllowsPrompt
      );
    }

    const scenarioFileLabel = form.querySelector('[data-material-label="scenario"]');
    if (scenarioFileLabel) {
      scenarioFileLabel.textContent = `${scenarioLabel}上传`;
      scenarioFileLabel.classList.toggle('hidden', !scenarioAllowsUpload);
    }
    const scenarioFieldWrapper = form.querySelector('[data-material-field="scenario"]');
    if (scenarioFieldWrapper) {
      scenarioFieldWrapper.classList.toggle('hidden', !scenarioAllowsUpload);
    }
    const scenarioFileInput = form.querySelector('input[name="scenario_asset"]');
    if (scenarioFileInput) {
      scenarioFileInput.disabled = !scenarioAllowsUpload;
    }
    const scenarioDescription = form.querySelector('[data-material-description="scenario"]');
    if (scenarioDescription) {
      scenarioDescription.textContent = scenarioAllowsPrompt
        ? `${scenarioLabel}描述（上传或 AI 生成时都会用到）`
        : `${scenarioLabel}描述`;
    }
    const scenarioTextarea = form.querySelector('[data-material-input="scenario"]');
    if (scenarioTextarea) {
      scenarioTextarea.placeholder =
        scenarioMaterial.promptPlaceholder || `描述${scenarioLabel}的氛围与细节`;
    }
    let scenarioChanged = false;
    if (!scenarioAllowsUpload) {
      if (state.scenario) {
        await deleteStoredAsset(state.scenario);
        state.scenario = null;
        scenarioChanged = true;
      }
      state.scenarioMode = 'prompt';
      if (scenarioUploadRadio) {
        scenarioUploadRadio.checked = false;
      }
      if (scenarioPromptRadio) {
        scenarioPromptRadio.checked = true;
      }
      if (inlinePreviews.scenario_asset) {
        inlinePreviews.scenario_asset.src = placeholderImages.scenario;
      }
    } else if (!scenarioAllowsPrompt && state.scenarioMode === 'prompt') {
      state.scenarioMode = 'upload';
      if (scenarioUploadRadio) {
        scenarioUploadRadio.checked = true;
      }
      if (scenarioPromptRadio) {
        scenarioPromptRadio.checked = false;
      }
    }
    if (scenarioChanged) {
      state.previewBuilt = false;
    }
    applyModeToInputs('scenario', state, form, inlinePreviews, { initial: true });

    const productMaterial = materials.product || {};
    const productLabel = getMaterialLabel('product', productMaterial);
    const productType = (productMaterial.type || 'image').toLowerCase();
    const productAllowsUpload = productType !== 'text' && productMaterial.allowsUpload !== false;
    const productAllowsPrompt = productType === 'text' || productMaterial.allowsPrompt !== false;
    state.productType = productType;
    state.productAllowsPrompt = productAllowsPrompt;
    state.productAllowsUpload = productAllowsUpload;

    const productToggleLabel = form.querySelector('[data-material-toggle-label="product"]');
    if (productToggleLabel) {
      productToggleLabel.textContent = `${productLabel}素材来源`;
    }
    const productToggle = form.querySelector('[data-mode-target="product"]');
    const productUploadOption = form.querySelector('[data-mode-option="product-upload"]');
    const productUploadRadio = productUploadOption?.querySelector('input[type="radio"]');
    if (productUploadOption) {
      productUploadOption.classList.toggle('hidden', !productAllowsUpload);
    }
    if (productUploadRadio) {
      productUploadRadio.disabled = !productAllowsUpload;
    }
    const productPromptOption = form.querySelector('[data-mode-option="product-prompt"]');
    const productPromptRadio = productPromptOption?.querySelector('input[type="radio"]');
    if (productPromptOption) {
      productPromptOption.classList.toggle('hidden', !productAllowsPrompt);
    }
    if (productPromptRadio) {
      productPromptRadio.disabled = !productAllowsPrompt;
    }
    if (productToggle) {
      productToggle.classList.toggle(
        'single-mode',
        !productAllowsUpload || !productAllowsPrompt
      );
    }

    const productFileLabel = form.querySelector('[data-material-label="product"]');
    if (productFileLabel) {
      productFileLabel.textContent = `${productLabel}上传`;
      productFileLabel.classList.toggle('hidden', !productAllowsUpload);
    }
    const productFieldWrapper = form.querySelector('[data-material-field="product"]');
    if (productFieldWrapper) {
      productFieldWrapper.classList.toggle('hidden', !productAllowsUpload);
    }
    const productFileInput = form.querySelector('input[name="product_asset"]');
    if (productFileInput) {
      productFileInput.disabled = !productAllowsUpload;
    }
    const productPromptContainer = form.querySelector('[data-material-prompt="product"]');
    if (productPromptContainer) {
      productPromptContainer.classList.toggle('hidden', !productAllowsPrompt);
    }
    const productPromptLabel = form.querySelector('[data-material-prompt-label="product"]');
    if (productPromptLabel) {
      productPromptLabel.textContent = productAllowsPrompt
        ? `${productLabel}生成描述（可选补充）`
        : `${productLabel}说明`;
    }
    const productPromptInput = form.querySelector('[data-material-input="product-prompt"]');
    if (productPromptInput) {
      productPromptInput.placeholder =
        productMaterial.promptPlaceholder || `补充${productLabel}的材质、角度等信息`;
    }
    let productChanged = false;
    if (!productAllowsUpload) {
      if (state.product) {
        await deleteStoredAsset(state.product);
        state.product = null;
        productChanged = true;
      }
      state.productMode = 'prompt';
      if (productUploadRadio) {
        productUploadRadio.checked = false;
      }
      if (productPromptRadio) {
        productPromptRadio.checked = true;
      }
      if (inlinePreviews.product_asset) {
        inlinePreviews.product_asset.src = placeholderImages.product;
      }
    } else if (!productAllowsPrompt && state.productMode === 'prompt') {
      state.productMode = 'upload';
      if (productUploadRadio) {
        productUploadRadio.checked = true;
      }
      if (productPromptRadio) {
        productPromptRadio.checked = false;
      }
    }
    if (productChanged) {
      state.previewBuilt = false;
    }
    applyModeToInputs('product', state, form, inlinePreviews, { initial: true });

    const galleryMaterial = materials.gallery || {};
    const galleryLabel = getMaterialLabel('gallery', galleryMaterial);
    const galleryType = (galleryMaterial.type || 'image').toLowerCase();
    const galleryAllowsUpload = galleryType !== 'text' && galleryMaterial.allowsUpload !== false;
    const galleryAllowsPrompt =
      galleryType === 'text' || galleryMaterial.allowsPrompt !== false;
    const slotCount = Array.isArray(spec?.gallery?.items)
      ? spec.gallery.items.length
      : null;
    const configuredCount = Number(galleryMaterial.count);
    const galleryLimit = Number.isFinite(configuredCount) && configuredCount > 0
      ? configuredCount
      : slotCount || state.galleryLimit || 4;
    state.galleryLabel = galleryLabel;
    state.galleryAllowsPrompt = galleryAllowsPrompt;
    state.galleryAllowsUpload = galleryAllowsUpload;
    state.galleryType = galleryType;
    if (state.galleryLimit !== galleryLimit) {
      const removed = state.galleryEntries.splice(galleryLimit);
      await Promise.all(
        removed.map((entry) => deleteStoredAsset(entry.asset))
      );
      state.galleryLimit = galleryLimit;
    } else {
      state.galleryLimit = galleryLimit;
    }
    if (!galleryAllowsUpload) {
      await Promise.all(
        state.galleryEntries.map(async (entry) => {
          if (entry.asset) {
            await deleteStoredAsset(entry.asset);
            entry.asset = null;
          }
          entry.mode = 'prompt';
        })
      );
      state.previewBuilt = false;
    } else if (!galleryAllowsPrompt) {
      state.galleryEntries.forEach((entry) => {
        if (entry.mode === 'prompt') {
          entry.mode = 'upload';
          entry.prompt = '';
        }
      });
      state.previewBuilt = false;
    }

    const galleryLabelElement = document.querySelector('[data-gallery-label]');
    if (galleryLabelElement) {
      galleryLabelElement.textContent = `${galleryLabel}（${galleryLimit} 项，支持多选）`;
    }
    const galleryDescription = document.querySelector('[data-gallery-description]');
    if (galleryDescription) {
      galleryDescription.textContent = !galleryAllowsUpload
        ? `每个条目需通过文字描述生成，共 ${galleryLimit} 项，请填写系列说明。`
        : galleryAllowsPrompt
        ? `每个条目由一张图像与系列说明组成，可上传或使用 AI 生成，共需 ${galleryLimit} 项。`
        : `请上传 ${galleryLimit} 张${galleryLabel}并填写对应说明。`;
    }
    const galleryUploadButton = document.querySelector('[data-gallery-upload]');
    if (galleryUploadButton) {
      galleryUploadButton.textContent = `上传${galleryLabel}`;
      galleryUploadButton.classList.toggle('hidden', !galleryAllowsUpload);
      galleryUploadButton.disabled = !galleryAllowsUpload;
    }
    const galleryPromptButton = document.querySelector('[data-gallery-prompt]');
    if (galleryPromptButton) {
      const promptText = galleryLabel.includes('条目')
        ? '添加 AI 生成条目'
        : `添加 AI 生成${galleryLabel}`;
      galleryPromptButton.textContent = promptText;
      galleryPromptButton.classList.toggle('hidden', !galleryAllowsPrompt);
    }

    renderGalleryItems(state, galleryItemsContainer, {
      previewElements,
      layoutStructure,
      previewContainer,
      statusElement,
      form,
      inlinePreviews,
      onChange: refreshPreview,
      allowPrompt: galleryAllowsPrompt,
      forcePromptOnly: !galleryAllowsUpload,
      promptPlaceholder:
        galleryMaterial.promptPlaceholder || '描述要生成的小图内容',
    });
    refreshPreview();
  }

  async function refreshTemplatePreviewStage1(templateId) {
  if (!templateCanvasStage1) return;
  try {
    const assets =  await App.utils.ensureTemplateAssets(templateId); // 原有：加载模板资源 {entry,spec,image}
    await applyTemplateMaterialsStage1(assets.spec);       // 原有：同步材料开关/占位说明等

    const ctx = templateCanvasStage1.getContext('2d');
    if (!ctx) return;
    const { width, height } = templateCanvasStage1;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);

    const img = assets.image;
    const scale = Math.min(width / img.width, height / img.height);
    const dw = img.width * scale;
    const dh = img.height * scale;
    const ox = (width - dw) / 2;
    const oy = (height - dh) / 2;
    ctx.drawImage(img, ox, oy, dw, dh);

    if (templateDescriptionStage1) {
      templateDescriptionStage1.textContent = assets.entry?.description || '';
    }
  } catch (err) {
    console.error('[template preview] failed:', err);
    if (templateDescriptionStage1) {
      templateDescriptionStage1.textContent = '模板预览加载失败，请检查 templates 资源。';
    }
    const ctx = templateCanvasStage1?.getContext?.('2d');
    if (ctx) {
      ctx.clearRect(0, 0, templateCanvasStage1.width, templateCanvasStage1.height);
      ctx.fillStyle = '#f4f5f7';
      ctx.fillRect(0, 0, templateCanvasStage1.width, templateCanvasStage1.height);
      ctx.fillStyle = '#6b7280';
      ctx.font = '16px "Noto Sans SC", sans-serif';
      ctx.fillText('模板预览加载失败', 24, 48);
    }
  }
  }
async function mountTemplateChooserStage1() {
  if (!templateSelectStage1) return;

  // 1) 加载 registry（保持原名）
  try {
    templateRegistry = await App.utils.loadTemplateRegistry();
  } catch (e) {
    console.error('[registry] load failed:', e);
    setStatus(statusElement, '无法加载模板列表，请检查 templates/registry.json 与静态路径。', 'warning');
    return;
  }
  if (!Array.isArray(templateRegistry) || templateRegistry.length === 0) {
    setStatus(statusElement, '模板列表为空，请确认 templates/registry.json 格式。', 'warning');
    return;
  }

  // 2) 填充下拉
  templateSelectStage1.innerHTML = '';
  templateRegistry.forEach((entry) => {
    const opt = document.createElement('option');
    opt.value = entry.id;
    opt.textContent = entry.name || entry.id;
    templateSelectStage1.appendChild(opt);
  });

  // 3) 恢复/设置默认选项
  const stored = loadStage1Data();
  if (stored?.template_id) {
    state.templateId = stored.template_id;
    state.templateLabel = stored.template_label || '';
  } else {
    const first = templateRegistry[0];
    state.templateId = first.id;
    state.templateLabel = first.name || '';
  }
  templateSelectStage1.value = state.templateId;

  // 4) 预览一次
  await refreshTemplatePreviewStage1(state.templateId);

  // 立即持久化一次（不必等“构建预览”）
  const quickPersist = () => {
    try {
      const relaxedPayload = collectStage1Data(form, state, { strict: false });
      currentLayoutPreview = updatePosterPreview(
        relaxedPayload,
        state,
        previewElements,
        layoutStructure,
        previewContainer
      );
      const serialised = serialiseStage1Data(relaxedPayload, state, currentLayoutPreview, false);
      saveStage1Data(serialised, { preserveStage2: false });
    } catch (e) {
      console.warn('[template persist] skipped:', e);
    }
  };
  quickPersist();

  // 5) 绑定切换
  templateSelectStage1.addEventListener('change', async (ev) => {
    const value = ev.target.value || DEFAULT_STAGE1.template_id;
    state.templateId = value;
    const entry = templateRegistry.find((x) => x.id === value);
    state.templateLabel = entry?.name || '';

    state.previewBuilt = false; // 切换模板 => 预览需重建
    setStatus(statusElement, '已切换模板，请重新构建版式预览或继续到环节 2 生成。', 'info');

    quickPersist();
    await refreshTemplatePreviewStage1(value);
  });
}

// 注意：不要用顶层 await
void mountTemplateChooserStage1();
  if (templateSelectStage1) {
    App.utils.loadTemplateRegistry()
      .then(async (registry) => {
        templateRegistry = registry;
        templateSelectStage1.innerHTML = '';
        registry.forEach((entry) => {
          const option = document.createElement('option');
          option.value = entry.id;
          option.textContent = entry.name;
          templateSelectStage1.appendChild(option);
        });
        const activeEntry = registry.find((entry) => entry.id === state.templateId);
        if (!activeEntry && registry[0]) {
          state.templateId = registry[0].id;
          state.templateLabel = registry[0].name || '';
        } else if (activeEntry) {
          state.templateLabel = activeEntry.name || state.templateLabel;
        }
        templateSelectStage1.value = state.templateId;
        await refreshTemplatePreviewStage1(state.templateId);
      })
      .catch((error) => {
        console.error(error);
        setStatus(statusElement, '无法加载模板列表，请检查 templates 目录。', 'warning');
      });

    templateSelectStage1.addEventListener('change', async (event) => {
      const value = event.target.value || DEFAULT_STAGE1.template_id;
      state.templateId = value;
      const entry = templateRegistry.find((item) => item.id === value);
      state.templateLabel = entry?.name || '';
      state.previewBuilt = false;
      refreshPreview();
      await refreshTemplatePreviewStage1(value);
    });
  }

  attachSingleImageHandler(
    form.querySelector('input[name="brand_logo"]'),
    'brandLogo',
    inlinePreviews.brand_logo,
    state,
    refreshPreview,
    statusElement
  );
  attachSingleImageHandler(
    form.querySelector('input[name="scenario_asset"]'),
    'scenario',
    inlinePreviews.scenario_asset,
    state,
    refreshPreview,
    statusElement
  );
  attachSingleImageHandler(
    form.querySelector('input[name="product_asset"]'),
    'product',
    inlinePreviews.product_asset,
    state,
    refreshPreview,
    statusElement
  );

  bindSlotGenerationButtons(form, state, inlinePreviews, {
    refreshPreview,
    statusElement,
  });

  renderGalleryItems(state, galleryItemsContainer, {
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement,
    form,
    inlinePreviews,
    onChange: refreshPreview,
    allowPrompt: state.galleryAllowsPrompt,
    forcePromptOnly: state.galleryAllowsUpload === false,
    promptPlaceholder:
      state.templateSpec?.materials?.gallery?.promptPlaceholder ||
      '描述要生成的小图内容',
  });

  refreshPreview();

  if (galleryButton && galleryFileInput) {
    galleryButton.addEventListener('click', () => {
      if (!state.galleryAllowsUpload) {
        setStatus(
          statusElement,
          `${state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery}由模板限定为 AI 生成，请通过“添加 AI 生成条目”补充素材。`,
          'info'
        );
        return;
      }
      galleryFileInput.click();
    });

    galleryFileInput.addEventListener('change', async (event) => {
      if (!state.galleryAllowsUpload) {
        event.target.value = '';
        setStatus(
          statusElement,
          `${state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery}当前仅支持文字描述生成。`,
          'warning'
        );
        return;
      }
      const files = Array.from(event.target.files || []);
      if (!files.length) {
        return;
      }
      const limit = state.galleryLimit || 4;
      const remaining = Math.max(0, limit - state.galleryEntries.length);
      if (remaining <= 0) {
        setStatus(
          statusElement,
          `最多仅支持上传 ${limit} 张${state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery}。`,
          'warning'
        );
        galleryFileInput.value = '';
        return;
      }

      const selected = files.slice(0, remaining);
      for (const file of selected) {
        try {
          const asset = await prepareAssetFromFile('gallery', file, null, statusElement);
          state.galleryEntries.push({
            id: createId(),
            caption: '',
            asset,
            mode: 'upload',
            prompt: '',
          });
        } catch (error) {
          console.error(error);
          setStatus(statusElement, '上传或读取底部产品小图时发生错误。', 'error');
        }
      }
      galleryFileInput.value = '';
      state.previewBuilt = false;
      renderGalleryItems(state, galleryItemsContainer, {
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement,
        form,
        inlinePreviews,
        onChange: refreshPreview,
        allowPrompt: state.galleryAllowsPrompt,
        forcePromptOnly: state.galleryAllowsUpload === false,
        promptPlaceholder:
          state.templateSpec?.materials?.gallery?.promptPlaceholder ||
          '描述要生成的小图内容',
      });
      refreshPreview();
    });
  }

  if (galleryPlaceholderButton) {
    galleryPlaceholderButton.addEventListener('click', () => {
      if (!state.galleryAllowsPrompt) {
        setStatus(
          statusElement,
          `${state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery}仅支持上传图像素材。`,
          'info'
        );
        return;
      }
      const limit = state.galleryLimit || 4;
      if (state.galleryEntries.length >= limit) {
        setStatus(
          statusElement,
          `最多仅支持 ${limit} 个${state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery}条目。`,
          'warning'
        );
        return;
      }
      state.galleryEntries.push({
        id: createId(),
        caption: '',
        asset: null,
        mode: 'prompt',
        prompt: '',
      });
      state.previewBuilt = false;
      renderGalleryItems(state, galleryItemsContainer, {
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement,
        form,
        inlinePreviews,
        onChange: refreshPreview,
        allowPrompt: state.galleryAllowsPrompt,
        forcePromptOnly: state.galleryAllowsUpload === false,
        promptPlaceholder:
          state.templateSpec?.materials?.gallery?.promptPlaceholder ||
          '描述要生成的小图内容',
      });
      refreshPreview();
    });
  }

  form.addEventListener('input', () => {
    state.previewBuilt = false;
    refreshPreview();
  });

  buildPreviewButton.addEventListener('click', () => {
    const relaxedPayload = collectStage1Data(form, state, { strict: false });
    currentLayoutPreview = updatePosterPreview(
      relaxedPayload,
      state,
      previewElements,
      layoutStructure,
      previewContainer
    );

    try {
      const strictPayload = collectStage1Data(form, state, { strict: true });
      state.previewBuilt = true;
      const serialised = serialiseStage1Data(
        strictPayload,
        state,
        currentLayoutPreview,
        true
      );
      saveStage1Data(serialised);
      setStatus(statusElement, '版式预览已构建，可继续下一环节。', 'success');
    } catch (error) {
      console.warn(error);
      state.previewBuilt = false;
      const serialised = serialiseStage1Data(
        relaxedPayload,
        state,
        currentLayoutPreview,
        false
      );
      saveStage1Data(serialised);
      const reason = error?.message || '请补全必填素材。';
      setStatus(
        statusElement,
        `预览已更新，但${reason.replace(/^[，。]?/, '')}`,
        'warning'
      );
    }
  });

  nextButton.addEventListener('click', () => {
    try {
      const payload = collectStage1Data(form, state, { strict: true });
      currentLayoutPreview = updatePosterPreview(
        payload,
        state,
        previewElements,
        layoutStructure,
        previewContainer
      );
      state.previewBuilt = true;
      const serialised = serialiseStage1Data(payload, state, currentLayoutPreview, true);
      saveStage1Data(serialised);
      setStatus(statusElement, '素材已保存，正在跳转至环节 2。', 'info');
      window.location.href = 'stage2.html';
    } catch (error) {
      console.error(error);
      setStatus(statusElement, error.message || '请先完成版式预览后再继续。', 'error');
    }
  });
}

function applyStage1Defaults(form) {
  for (const [key, value] of Object.entries(DEFAULT_STAGE1)) {
    const element = form.elements.namedItem(key);
    if (element && typeof value === 'string') {
      element.value = value;
    }
  }

  const featureInputs = form.querySelectorAll('input[name="features"]');
  featureInputs.forEach((input, index) => {
    input.value = DEFAULT_STAGE1.features[index] ?? '';
  });

  const scenarioModeInputs = form.querySelectorAll('input[name="scenario_mode"]');
  scenarioModeInputs.forEach((input) => {
    input.checked = input.value === DEFAULT_STAGE1.scenario_mode;
  });

  const productModeInputs = form.querySelectorAll('input[name="product_mode"]');
  productModeInputs.forEach((input) => {
    input.checked = input.value === DEFAULT_STAGE1.product_mode;
  });

  const productPrompt = form.elements.namedItem('product_prompt');
  if (productPrompt && 'value' in productPrompt) {
    productPrompt.value = '';
  }
}

function updateInlinePlaceholders(inlinePreviews) {
  if (inlinePreviews.brand_logo) inlinePreviews.brand_logo.src = placeholderImages.brandLogo;
  if (inlinePreviews.scenario_asset) inlinePreviews.scenario_asset.src = placeholderImages.scenario;
  if (inlinePreviews.product_asset) inlinePreviews.product_asset.src = placeholderImages.product;
}

async function applyStage1DataToForm(data, form, state, inlinePreviews) {
  for (const key of ['brand_name', 'agent_name', 'scenario_image', 'product_name', 'title', 'subtitle']) {
    const element = form.elements.namedItem(key);
    if (element && typeof data[key] === 'string') {
      element.value = data[key];
    }
  }

  const features = Array.isArray(data.features) && data.features.length
    ? data.features
    : DEFAULT_STAGE1.features;
  const featureInputs = form.querySelectorAll('input[name="features"]');
  featureInputs.forEach((input, index) => {
    input.value = features[index] ?? '';
  });

  const scenarioModeValue = data.scenario_mode || DEFAULT_STAGE1.scenario_mode;
  const productModeValue = data.product_mode || DEFAULT_STAGE1.product_mode;
  state.scenarioMode = scenarioModeValue;
  state.productMode = productModeValue;

  const scenarioModeInputs = form.querySelectorAll('input[name="scenario_mode"]');
  scenarioModeInputs.forEach((input) => {
    input.checked = input.value === scenarioModeValue;
  });

  const productModeInputs = form.querySelectorAll('input[name="product_mode"]');
  productModeInputs.forEach((input) => {
    input.checked = input.value === productModeValue;
  });

  const productPrompt = form.elements.namedItem('product_prompt');
  if (productPrompt && 'value' in productPrompt) {
    productPrompt.value =
      typeof data.product_prompt === 'string' ? data.product_prompt : '';
  }

  state.brandLogo = await rehydrateStoredAsset(data.brand_logo);
  updateMaterialUrlDisplay('brand_logo', state.brandLogo);
  state.scenario = await rehydrateStoredAsset(data.scenario_asset);
  state.product = await rehydrateStoredAsset(data.product_asset);
  state.galleryEntries = Array.isArray(data.gallery_entries)
      ? await Promise.all(
        data.gallery_entries.map(async (entry) => ({
          id: entry.id || createId(),
          caption: entry.caption || '',
          asset: await rehydrateStoredAsset(entry.asset),
          mode:
            entry.mode === 'logo' || entry.mode === 'logo_fallback'
              ? 'upload'
              : entry.mode || 'upload',
          prompt: entry.prompt || '',
        }))
      )
    : [];
  state.galleryLimit = typeof data.gallery_limit === 'number' ? data.gallery_limit : state.galleryLimit;
  state.galleryLabel = data.gallery_label || state.galleryLabel;
  state.galleryAllowsPrompt = data.gallery_allows_prompt !== false;
  state.galleryAllowsUpload = data.gallery_allows_upload !== false;
  if (state.galleryEntries.length > state.galleryLimit) {
    state.galleryEntries = state.galleryEntries.slice(0, state.galleryLimit);
  }
  state.templateId = data.template_id || DEFAULT_STAGE1.template_id;
  state.templateLabel = data.template_label || '';

  applyModeToInputs('scenario', state, form, inlinePreviews);
  applyModeToInputs('product', state, form, inlinePreviews);

  if (inlinePreviews.brand_logo) {
    inlinePreviews.brand_logo.src = state.brandLogo?.dataUrl || placeholderImages.brandLogo;
  }
  if (inlinePreviews.scenario_asset) {
    inlinePreviews.scenario_asset.src = state.scenario?.dataUrl || placeholderImages.scenario;
  }
  if (inlinePreviews.product_asset) {
    inlinePreviews.product_asset.src = state.product?.dataUrl || placeholderImages.product;
  }
}

function attachSingleImageHandler(
  input,
  key,
  inlinePreview,
  state,
  refreshPreview,
  statusElement
) {
  if (!input) return;
  input.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) {
      await deleteStoredAsset(state[key]);
      state[key] = null;
      state.previewBuilt = false;
      if (inlinePreview) {
        const placeholder =
          key === 'brandLogo'
            ? placeholderImages.brandLogo
            : key === 'scenario'
            ? placeholderImages.scenario
            : placeholderImages.product;
        inlinePreview.src = placeholder;
      }
      if (key === 'brandLogo') {
        updateMaterialUrlDisplay('brand_logo', state[key]);
      }
      refreshPreview();
      return;
    }
    try {
      const folderMap = {
        brandLogo: 'brand-logo',
        scenario: 'scenario',
        product: 'product',
      };
      const folder = folderMap[key] || 'uploads';
      const requireUploadOptions =
        key === 'brandLogo'
          ? {
              requireUpload: true,
              requireUploadMessage:
                '品牌 Logo 必须上传到 R2/GCS，仅传递 URL 或 Key。',
            }
          : {};
      state[key] = await prepareAssetFromFile(
        folder,
        file,
        state[key],
        statusElement,
        requireUploadOptions
      );
      if (inlinePreview) {
        inlinePreview.src = state[key]?.dataUrl ||
          (key === 'brandLogo'
            ? placeholderImages.brandLogo
            : key === 'scenario'
            ? placeholderImages.scenario
            : placeholderImages.product);
      }
      if (key === 'brandLogo') {
        updateMaterialUrlDisplay('brand_logo', state[key]);
      }
      state.previewBuilt = false;
      refreshPreview();
    } catch (error) {
      console.error(error);
      const message =
        error instanceof Error
          ? error.message || '处理图片素材时发生错误，请重试。'
          : '处理图片素材时发生错误，请重试。';
      setStatus(statusElement, message, 'error');
    }
  });
}

function applyModeToInputs(target, state, form, inlinePreviews, options = {}) {
  const { initial = false } = options;
  const mode = target === 'scenario' ? state.scenarioMode : state.productMode;
  const fileInput = form.querySelector(`input[name="${target}_asset"]`);
  if (fileInput) {
    const allowsUpload =
      target === 'scenario'
        ? state.scenarioAllowsUpload !== false
        : state.productAllowsUpload !== false;
    fileInput.disabled = mode === 'prompt' || !allowsUpload;
  }
  const promptField = form.querySelector(`[data-mode-visible="${target}:prompt"]`);
  if (promptField) {
    if (mode === 'prompt') {
      promptField.classList.add('mode-visible');
    } else {
      promptField.classList.remove('mode-visible');
    }
  }

  if (!initial) {
    const inlineKey = `${target}_asset`;
    const inlinePreview = inlinePreviews?.[inlineKey];
    if (inlinePreview && !state[target]?.dataUrl) {
      inlinePreview.src =
        target === 'scenario' ? placeholderImages.scenario : placeholderImages.product;
    }
  }
}

async function switchAssetMode(target, mode, context) {
  const { form, state, inlinePreviews, refreshPreview } = context;
  const assetKey = target === 'scenario' ? 'scenario' : 'product';
  const previousMode = target === 'scenario' ? state.scenarioMode : state.productMode;
  const allowsPrompt =
    target === 'scenario'
      ? state.scenarioAllowsPrompt !== false
      : state.productAllowsPrompt !== false;
  const allowsUpload =
    target === 'scenario'
      ? state.scenarioAllowsUpload !== false
      : state.productAllowsUpload !== false;
  if (mode === 'prompt' && !allowsPrompt) {
    mode = 'upload';
  }
  if (mode === 'upload' && !allowsUpload) {
    mode = 'prompt';
  }
  if (previousMode === mode) {
    applyModeToInputs(target, state, form, inlinePreviews, { initial: true });
    return;
  }

  if (target === 'scenario') {
    state.scenarioMode = mode;
  } else {
    state.productMode = mode;
  }

  applyModeToInputs(target, state, form, inlinePreviews);

  if (mode === 'prompt') {
    await deleteStoredAsset(state[assetKey]);
    state[assetKey] = null;
    const inlineKey = `${target}_asset`;
    const inlinePreview = inlinePreviews?.[inlineKey];
    if (inlinePreview) {
      inlinePreview.src =
        target === 'scenario' ? placeholderImages.scenario : placeholderImages.product;
    }
  }

  state.previewBuilt = false;
  refreshPreview?.();
}

function renderGalleryItems(state, container, options = {}) {
  const {
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement,
    onChange,
    allowPrompt = true,
    forcePromptOnly = false,
    promptPlaceholder = '描述要生成的小图内容',
    form,
    inlinePreviews,
  } = options;
  if (!container) return;
  container.innerHTML = '';

  const limit = state.galleryLimit || 4;
  const label = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;
  const allowUpload = !forcePromptOnly;
  const allowPromptMode = forcePromptOnly ? true : allowPrompt;

  state.galleryEntries.slice(0, limit).forEach((entry, index) => {
    entry.mode = entry.mode || (allowUpload ? 'upload' : 'prompt');
    entry.prompt = typeof entry.prompt === 'string' ? entry.prompt : '';
    if (!allowUpload && entry.asset) {
      void deleteStoredAsset(entry.asset);
      entry.asset = null;
      state.previewBuilt = false;
    }
    if (!allowUpload) {
      entry.mode = 'prompt';
    } else if (!allowPromptMode && entry.mode === 'prompt') {
      entry.mode = 'upload';
      state.previewBuilt = false;
    }

    const placeholder = getGalleryPlaceholder(index, label);

    const item = document.createElement('div');
    item.classList.add('gallery-item', 'bottom-product-card');
    item.dataset.galleryIndex = String(index);
    item.dataset.id = entry.id;

    const header = document.createElement('div');
    header.classList.add('gallery-item-header');
    const title = document.createElement('span');
    title.classList.add('gallery-item-title');
    title.textContent = `${label} ${index + 1}`;
    header.appendChild(title);

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.classList.add('secondary');
    removeButton.textContent = '移除';
    removeButton.addEventListener('click', async () => {
      await deleteStoredAsset(entry.asset);
      state.galleryEntries = state.galleryEntries.filter((g) => g.id !== entry.id);
      state.previewBuilt = false;
      renderGalleryItems(state, container, {
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement,
        form,
        inlinePreviews,
        onChange,
        allowPrompt,
        forcePromptOnly,
        promptPlaceholder,
      });
      onChange?.();
    });

    const actions = document.createElement('div');
    actions.classList.add('gallery-item-actions');
    actions.appendChild(removeButton);
    header.appendChild(actions);
    item.appendChild(header);

    const modeToggle = document.createElement('div');
    modeToggle.classList.add('mode-toggle', 'gallery-mode-toggle');
    if (!allowUpload || !allowPromptMode) {
      modeToggle.classList.add('single-mode');
    }
    const modeLabel = document.createElement('span');
    if (!allowUpload && allowPromptMode) {
      modeLabel.textContent = '素材来源（模板限定：AI 生成）';
    } else if (allowUpload && !allowPromptMode) {
      modeLabel.textContent = '素材来源（模板限定：需上传图像）';
    } else {
      modeLabel.textContent = '素材来源';
    }
    modeToggle.appendChild(modeLabel);

    const radioName = `gallery_mode_${entry.id}`;
    let uploadRadio = null;
    if (allowUpload) {
      const uploadLabel = document.createElement('label');
      uploadRadio = document.createElement('input');
      uploadRadio.type = 'radio';
      uploadRadio.name = radioName;
      uploadRadio.value = 'upload';
      uploadLabel.appendChild(uploadRadio);
      uploadLabel.append(' 上传图像');
      modeToggle.appendChild(uploadLabel);
    }

    let promptRadio = null;
    if (allowPromptMode) {
      const promptLabel = document.createElement('label');
      promptRadio = document.createElement('input');
      promptRadio.type = 'radio';
      promptRadio.name = radioName;
      promptRadio.value = 'prompt';
      promptLabel.appendChild(promptRadio);
      promptLabel.append(' 文字生成');
      modeToggle.appendChild(promptLabel);
    }
    item.appendChild(modeToggle);

    const fileField = document.createElement('label');
    fileField.classList.add('field', 'file-field', 'gallery-file-field');
    fileField.innerHTML = `<span>上传${label}</span>`;
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.disabled = !allowUpload;
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      try {
        entry.asset = await prepareAssetFromFile('gallery', file, entry.asset, statusElement);
        previewImage.src = pickImageSrc(entry.asset) || placeholder;
        state.previewBuilt = false;
        onChange?.();
      } catch (error) {
        console.error(error);
        setStatus(statusElement, '上传或读取底部产品小图时发生错误。', 'error');
      }
    });
    if (!allowUpload) {
      fileField.classList.add('mode-hidden');
    }
    fileField.appendChild(fileInput);
    item.appendChild(fileField);

    const previewWrapper = document.createElement('div');
    previewWrapper.classList.add('gallery-item-preview');
    previewWrapper.dataset.galleryIndex = String(index);
    const previewImage = document.createElement('img');
    previewImage.alt = `${label} ${index + 1} 预览`;
    previewImage.src = pickImageSrc(entry.asset) || placeholder;
    previewImage.dataset.role = 'gallery-preview';
    previewImage.dataset.index = String(index);
    previewImage.dataset.galleryIndex = String(index);
    previewImage.classList.add('slot-preview');
    previewWrapper.appendChild(previewImage);
    item.appendChild(previewWrapper);

    const captionField = document.createElement('label');
    captionField.classList.add('field', 'gallery-caption');
    captionField.innerHTML = `<span>${label}文案</span>`;
    const captionInput = document.createElement('input');
    captionInput.type = 'text';
    captionInput.value = entry.caption || '';
    captionInput.placeholder = '请输入对应系列说明';
    captionInput.addEventListener('input', () => {
      entry.caption = captionInput.value;
      state.previewBuilt = false;
      onChange?.();
    });
    captionField.appendChild(captionInput);
    item.appendChild(captionField);

    const promptField = document.createElement('label');
    promptField.classList.add('field', 'gallery-prompt', 'optional');
    promptField.innerHTML = '<span>AI 生成描述</span>';
    const promptTextarea = document.createElement('textarea');
    promptTextarea.rows = 2;
    promptTextarea.placeholder = promptPlaceholder;
    promptTextarea.value = entry.prompt || '';
    promptTextarea.dataset.role = 'gallery-prompt';
    promptTextarea.dataset.index = String(index);
    promptTextarea.addEventListener('input', () => {
      entry.prompt = promptTextarea.value;
      state.previewBuilt = false;
      onChange?.();
      refreshGalleryGenerateState(entry.mode === 'prompt');
    });
    promptField.appendChild(promptTextarea);
    item.appendChild(promptField);

    const generateButton = document.createElement('button');
    generateButton.type = 'button';
    generateButton.textContent = `AI 生成底部产品小图 ${index + 1}`;
    generateButton.classList.add('secondary');
    generateButton.dataset.role = 'gallery-generate';
    generateButton.dataset.index = String(index);
    item.appendChild(generateButton);

    const refreshGalleryGenerateState = (isPromptMode) => {
      const hasPromptText = Boolean((promptTextarea.value || '').trim());
      generateButton.disabled = !allowPromptMode || !isPromptMode || !hasPromptText;
    };

    async function applyGalleryMode(mode, options = {}) {
      const { initial = false } = options;
      let resolvedMode = mode;
      if (!allowUpload) {
        resolvedMode = 'prompt';
      } else if (!allowPromptMode && mode === 'prompt') {
        resolvedMode = 'upload';
      }
      entry.mode = resolvedMode;
      const isPrompt = resolvedMode === 'prompt';

      fileInput.disabled = !allowUpload || isPrompt;
      if (allowUpload) {
        fileField.classList.toggle('mode-hidden', isPrompt);
      } else {
        fileField.classList.add('mode-hidden');
      }

      if (allowPromptMode) {
        promptField.classList.remove('hidden');
        promptField.classList.toggle('mode-visible', isPrompt);
        promptTextarea.disabled = !isPrompt;
      } else {
        promptField.classList.add('hidden');
        promptTextarea.disabled = true;
      }

      if (isPrompt) {
        if ((!allowUpload && entry.asset) || (allowUpload && entry.asset && !initial)) {
          await deleteStoredAsset(entry.asset);
          entry.asset = null;
        }
        previewImage.src = placeholder;
      } else {
        previewImage.src = pickImageSrc(entry.asset) || placeholder;
      }

      if (allowPromptMode) {
        refreshGalleryGenerateState(isPrompt);
      }

      if (!initial) {
        state.previewBuilt = false;
        onChange?.();
      }
    }

    if (uploadRadio) {
      uploadRadio.addEventListener('change', () => {
        if (uploadRadio.checked) {
          void applyGalleryMode('upload');
        }
      });
      uploadRadio.checked = entry.mode !== 'prompt';
    }

    if (promptRadio) {
      promptRadio.addEventListener('change', () => {
        if (promptRadio.checked) {
          void applyGalleryMode('prompt');
        }
      });
      promptRadio.checked = entry.mode === 'prompt';
    }

    if (!allowPromptMode) {
      promptField.classList.add('hidden');
      promptTextarea.disabled = true;
    }

    void applyGalleryMode(entry.mode, { initial: true });

    container.appendChild(item);
  });

  bindSlotGenerationButtons(form, state, inlinePreviews, {
    refreshPreview: onChange,
    statusElement,
  });
}
function collectStage1Data(form, state, { strict = false } = {}) {
  const formData = new FormData(form);
  const payload = {
    brand_name: formData.get('brand_name')?.toString().trim() || '',
    agent_name: formData.get('agent_name')?.toString().trim() || '',
    scenario_image: formData.get('scenario_image')?.toString().trim() || '',
    product_name: formData.get('product_name')?.toString().trim() || '',
    title: formData.get('title')?.toString().trim() || '',
    subtitle: formData.get('subtitle')?.toString().trim() || '',
  };

  const features = formData
    .getAll('features')
    .map((feature) => feature.toString().trim())
    .filter((feature) => feature.length > 0);

  payload.features = features;

  const galleryLimit = state.galleryLimit || 4;
  const galleryLabel = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;

  const galleryEntries = state.galleryEntries.slice(0, galleryLimit).map((entry) => ({
    id: entry.id,
    caption: entry.caption.trim(),
    asset: entry.asset,
    mode: entry.mode || 'upload',
    prompt: entry.prompt?.trim() || null,
  }));

  const validGalleryEntries = galleryEntries.filter((entry) =>
    entry.mode === 'prompt' ? Boolean(entry.prompt) : Boolean(entry.asset)
  );

  payload.series_description = validGalleryEntries.length
    ? validGalleryEntries
        .map((entry, index) => `${galleryLabel}${index + 1}：${entry.caption || '系列说明待补充'}`)
        .join(' / ')
    : '';

  payload.brand_logo = state.brandLogo;
  payload.scenario_asset = state.scenario;
  payload.product_asset = state.product;
  payload.gallery_entries = galleryEntries;
  payload.template_id = state.templateId || DEFAULT_STAGE1.template_id;
  payload.template_label = state.templateLabel || '';
  payload.scenario_mode = state.scenarioMode || 'upload';
  payload.product_mode = state.productMode || 'upload';
  const productPromptValue = formData.get('product_prompt')?.toString().trim() || '';
  payload.product_prompt = productPromptValue || null;
  payload.scenario_prompt =
    payload.scenario_mode === 'prompt' ? payload.scenario_image : null;
  payload.gallery_label = galleryLabel;
  payload.gallery_limit = galleryLimit;
  payload.gallery_allows_prompt = state.galleryAllowsPrompt !== false;

  if (strict) {
    const missing = [];
    for (const [key, value] of Object.entries(payload)) {
      if (
        [
          'brand_logo',
          'scenario_asset',
          'product_asset',
          'gallery_entries',
          'scenario_mode',
          'product_mode',
          'product_prompt',
          'scenario_prompt',
        ].includes(key)
      ) {
        continue;
      }
      if (typeof value === 'string' && !value) {
        missing.push(key);
      }
    }
    if (payload.features.length < 3) {
      throw new Error('请填写至少 3 条产品功能点。');
    }
    if (galleryLimit > 0 && validGalleryEntries.length < galleryLimit) {
      throw new Error(
        `请准备至少 ${galleryLimit} 个${galleryLabel}（上传或 AI 生成）并填写对应文案。`
      );
    }
    const captionsIncomplete = validGalleryEntries.some((entry) => !entry.caption);
    if (captionsIncomplete) {
      throw new Error(`请为每个${galleryLabel}填写文案说明。`);
    }
    const promptMissing = galleryEntries.some(
      (entry) => entry.mode === 'prompt' && !entry.prompt
    );
    if (promptMissing) {
      throw new Error(`选择 AI 生成的${galleryLabel}需要提供文字描述。`);
    }
    if (missing.length) {
      throw new Error('请完整填写素材输入表单中的必填字段。');
    }
  }

  return payload;
}

async function generateSlotImage(slotType, index, promptText, stage1Data) {
  const apiCandidates = getApiCandidates(apiBaseInput?.value || null);
  if (!apiCandidates.length) {
    throw new Error('未配置后端 API 基址');
  }
  const prompt = (promptText || '').trim();
  if (!prompt) {
    throw new Error('请先填写提示词再生成图片');
  }

  const payload = {
    slot: slotType,
    index: index ?? null,
    prompt,
    template_id: stage1Data?.template_id || stage1Data?.templateId || null,
  };

  const data = await postJsonWithRetry(
    apiCandidates,
    '/api/generate-slot-image',
    payload,
    1
  );

  if (!data || !data.url) {
    throw new Error('生成图片失败，返回结果缺少 url');
  }

  return data;
}

function bindSlotGenerationButtons(form, state, inlinePreviews, options = {}) {
  const { refreshPreview, statusElement } = options;
  const posterForm = form || document.getElementById('poster-form');
  if (!posterForm) return;

  const scenarioPreview = document.getElementById('scenario_preview');
  const productPreview = document.getElementById('product_preview');

  const getStage1Snapshot = () => collectStage1Data(posterForm, state, { strict: false });

  const applyGeneratedAsset = (targetKey, asset, previewEl) => {
    if (!asset) return;
    state[targetKey] = asset;
    const modeKey = targetKey === 'scenario' ? 'scenarioMode' : 'productMode';
    state[modeKey] = 'upload';
    state.previewBuilt = false;

    const inlineKey = `${targetKey}_asset`;
    const inlineEl =
      inlinePreviews?.[inlineKey] ||
      posterForm.querySelector(`[data-inline-preview="${inlineKey}"]`);
    const src = pickImageSrc(asset);
    if (inlineEl && src) inlineEl.src = src;
    if (previewEl && src) previewEl.src = src;

    const uploadRadio = posterForm.querySelector(
      `input[name="${targetKey}_mode"][value="upload"]`
    );
    const promptRadio = posterForm.querySelector(
      `input[name="${targetKey}_mode"][value="prompt"]`
    );
    if (uploadRadio) uploadRadio.checked = true;
    if (promptRadio) promptRadio.checked = false;

    refreshPreview?.();
  };

  const bindButton = (buttonId, slotType, promptSelectors, previewEl) => {
    const button = document.getElementById(buttonId);
    if (!button || button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';

    const promptEl =
      promptSelectors.map((selector) => posterForm.querySelector(selector)).find(Boolean) ||
      null;

    const isPromptMode = () =>
      slotType === 'scenario'
        ? state.scenarioMode === 'prompt'
        : state.productMode === 'prompt';

    const refreshButtonState = () => {
      const promptValue = (promptEl?.value || '').trim();
      button.disabled = !isPromptMode() || !promptValue;
    };

    if (promptEl) {
      promptEl.addEventListener('input', refreshButtonState);
    }

    const modeInputs = posterForm.querySelectorAll(`input[name="${slotType}_mode"]`);
    modeInputs.forEach((input) => input.addEventListener('change', refreshButtonState));

    refreshButtonState();

    button.addEventListener('click', async () => {
      const prompt = promptEl?.value || '';
      if (!isPromptMode()) return;
      try {
        button.disabled = true;
        const snapshot = getStage1Snapshot();
        const { url, key } = await generateSlotImage(
          slotType,
          null,
          prompt,
          snapshot
        );
        const asset = buildGeneratedAssetFromUrl(url, key);
        applyGeneratedAsset(slotType === 'scenario' ? 'scenario' : 'product', asset, previewEl);
      } catch (err) {
        console.error(`[${slotType}] generate failed`, err);
        const detail = err?.responseJson?.detail || err?.responseJson;
        const quotaExceeded = err?.status === 429 && detail?.error === 'vertex_quota_exceeded';
        const message = quotaExceeded
          ? '图像生成配额已用尽，请稍后再试，或先上传现有素材。'
          : err?.message || '生成图片失败';
        if (statusElement) {
          setStatus(statusElement, message, 'error');
        } else {
          alert(message);
        }
      } finally {
        refreshButtonState();
      }
    });
  };

  bindButton(
    'btn-generate-scenario',
    'scenario',
    ['[data-role="scenario-positive-prompt"]', 'textarea[name="scenario_image"]'],
    scenarioPreview
  );

  bindButton(
    'btn-generate-product',
    'product',
    ['[data-role="product-positive-prompt"]', 'textarea[name="product_prompt"]'],
    productPreview
  );

  const galleryButtons = document.querySelectorAll('[data-role="gallery-generate"]');
  galleryButtons.forEach((btn) => {
    if (btn.dataset.bound === 'true') return;
    btn.dataset.bound = 'true';
    const index = Number(btn.getAttribute('data-index') || '0');
    btn.addEventListener('click', async () => {
      const promptEl = posterForm.querySelector(
        `[data-role="gallery-prompt"][data-index="${index}"]`
      );
      const prompt = promptEl?.value || '';
      try {
        btn.disabled = true;
        const snapshot = getStage1Snapshot();
        const { url, key } = await generateSlotImage('gallery', index, prompt, snapshot);

        if (!Array.isArray(state.galleryEntries)) {
          state.galleryEntries = [];
        }
        if (!state.galleryEntries[index]) {
          state.galleryEntries[index] = {
            id: `gallery-${index}-${Date.now()}`,
            caption: '',
            asset: null,
            prompt: '',
            mode: 'upload',
          };
        }

        state.galleryEntries[index].asset = buildGeneratedAssetFromUrl(url, key);
        state.galleryEntries[index].mode = 'upload';
        state.previewBuilt = false;

        const img = posterForm.querySelector(
          `[data-role="gallery-preview"][data-index="${index}"]`
        );
        const src = pickImageSrc(state.galleryEntries[index].asset);
        if (img && src) img.src = src;

        const logoFallback = pickImageSrc(state.brandLogo);
        applySlotImagePreview('gallery', index, src, { logoFallback });

        refreshPreview?.();
      } catch (err) {
        console.error(`[gallery ${index}] generate failed`, err);
        const detail = err?.responseJson?.detail || err?.responseJson;
        const quotaExceeded = err?.status === 429 && detail?.error === 'vertex_quota_exceeded';
        const message =
          quotaExceeded
            ? '图像生成配额已用尽，请稍后再试，或先上传现有素材。'
            : err?.message || `生成小图 ${index + 1} 失败`;
        if (statusElement) {
          setStatus(statusElement, message, 'error');
        } else {
          alert(message);
        }
      } finally {
        btn.disabled = false;
      }
    });
  });
}

function updatePosterPreview(payload, state, elements, layoutStructure, previewContainer) {
  const {
    brandLogo,
    brandName,
    agentName,
    scenarioImage,
    productImage,
    featureList,
    title,
    subtitle,
    gallery,
  } = elements;

  const layoutText = buildLayoutPreview(payload);

  if (layoutStructure) {
    layoutStructure.textContent = layoutText;
  }

  if (previewContainer) {
    previewContainer.classList.remove('hidden');
  }

  const assetSrc = (asset) => {
    if (!asset) return null;
    const candidates = [
      asset.remoteUrl,
      asset.url,
      asset.publicUrl,
      asset.dataUrl,
    ];
    return candidates.find(
      (value) => typeof value === 'string' && (HTTP_URL_RX.test(value) || value.startsWith('data:'))
    ) || null;
  };

  const logoFallback = assetSrc(state.brandLogo) || placeholderImages.brandLogo;

  if (brandLogo) {
    brandLogo.src = assetSrc(payload.brand_logo) || placeholderImages.brandLogo;
  }
  if (brandName) {
    brandName.textContent = payload.brand_name || '品牌名称';
  }
  if (agentName) {
    agentName.textContent = (payload.agent_name || '代理名 / 分销名').toUpperCase();
  }
  if (scenarioImage) {
    scenarioImage.src = assetSrc(payload.scenario_asset) || placeholderImages.scenario;
  }
  if (productImage) {
    productImage.src = assetSrc(payload.product_asset) || placeholderImages.product;
  }
  if (title) {
    title.textContent = payload.title || '标题文案';
  }
  if (subtitle) {
    subtitle.textContent = payload.subtitle || '副标题文案';
  }

  if (featureList) {
    const featuresForPreview = payload.features.length
      ? payload.features
      : DEFAULT_STAGE1.features;
    renderFeatureTags(featureList, featuresForPreview.slice(0, 3));
  }

  if (gallery) {
    gallery.innerHTML = '';
    const limit = state.galleryLimit || 4;
    const entries = state.galleryEntries.slice(0, limit);
    const galleryLabel = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;
    const total = Math.max(entries.length, limit);
    for (let index = 0; index < total; index += 1) {
      const entry = entries[index];
      const figure = document.createElement('figure');
      figure.dataset.galleryIndex = String(index);
      const img = document.createElement('img');
      const caption = document.createElement('figcaption');
      const gallerySrc = assetSrc(entry?.asset) || logoFallback;
      img.src = gallerySrc || getGalleryPlaceholder(index, galleryLabel);
      img.alt = `${galleryLabel} ${index + 1} 预览`;
      caption.textContent = entry?.caption || `${galleryLabel} ${index + 1}`;
      figure.appendChild(img);
      figure.appendChild(caption);
      gallery.appendChild(figure);
    }
  }

  return layoutText;
}

function buildLayoutPreview(payload) {
  const templateLine =
    payload.template_label || payload.template_id || DEFAULT_STAGE1.template_id;
  const logoLine = payload.brand_logo
    ? `已上传品牌 Logo（${payload.brand_name}）`
    : payload.brand_name || '品牌 Logo 待上传';
  const hasScenarioAsset = Boolean(payload.scenario_asset || payload.scenario_key);
  const scenarioLine = payload.scenario_mode === 'prompt'
    ? `AI 生成（描述：${payload.scenario_prompt || payload.scenario_image || '待补充'}）`
    : hasScenarioAsset
    ? `已上传应用场景图（描述：${payload.scenario_image || '待补充'}）`
    : payload.scenario_image || '应用场景描述待补充';
  const hasProductAsset = Boolean(payload.product_asset || payload.product_key);
  const productLine = payload.product_mode === 'prompt'
    ? `AI 生成（${payload.product_prompt || payload.product_name || '描述待补充'}）`
    : hasProductAsset
    ? `已上传 45° 渲染图（${payload.product_name || '主产品'}）`
    : payload.product_name || '主产品名称待补充';
  const galleryLabel = payload.gallery_label || MATERIAL_DEFAULT_LABELS.gallery;
  const galleryLimit = payload.gallery_limit || 4;

  const featuresPreview = (payload.features.length ? payload.features : DEFAULT_STAGE1.features)
    .map((feature, index) => `    - 功能点${index + 1}: ${feature}`)
    .join('\n');

  const galleryEntries = Array.isArray(payload.gallery_entries)
    ? payload.gallery_entries.filter((entry) =>
        entry.mode === 'prompt'
          ? Boolean(entry.prompt)
          : Boolean(entry.asset || entry.key)
      )
    : [];
  const gallerySummary = galleryEntries.length
    ? galleryEntries
        .map((entry, index) =>
          entry.mode === 'prompt'
            ? `    · ${galleryLabel}${index + 1}：AI 生成（${entry.prompt || '描述待补充'}）`
            : `    · ${galleryLabel}${index + 1}：${entry.caption || '系列说明待补充'}`
        )
        .join('\n')
    : `    · ${galleryLabel}待准备（可上传或 AI 生成 ${galleryLimit} 项素材，并附文字说明）。`;

  return `模板锁版\n  · 当前模板：${templateLine}\n\n顶部横条\n  · 品牌 Logo（左上）：${logoLine}\n  · 品牌代理名 / 分销名（右上）：${
    payload.agent_name || '代理名待填写'
  }\n\n左侧区域（约 40% 宽）\n  · 应用场景图：${scenarioLine}\n\n右侧区域（视觉中心）\n  · 主产品 45° 渲染图：${productLine}\n  · 功能点标注：\n${featuresPreview}\n\n中部标题（大号粗体红字）\n  · ${payload.title || '标题文案待补充'}\n\n底部区域（三视图或系列款式）\n${gallerySummary}\n\n角落副标题 / 标语（大号粗体红字）\n  · ${payload.subtitle || '副标题待补充'}\n\n主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）\n背景：浅灰或白色，保持留白与对齐。`;
}

function serialiseStage1Data(payload, state, layoutPreview, previewBuilt) {
  return {
    brand_name: payload.brand_name,
    agent_name: payload.agent_name,
    scenario_image: payload.scenario_image,
    product_name: payload.product_name,
    features: payload.features,
    title: payload.title,
    subtitle: payload.subtitle,
    series_description: payload.series_description,
    scenario_mode: state.scenarioMode || 'upload',
    product_mode: state.productMode || 'upload',
    product_prompt: payload.product_prompt,
    scenario_prompt: payload.scenario_prompt,
    brand_logo: serialiseAssetForStorage(state.brandLogo),
    scenario_asset: serialiseAssetForStorage(state.scenario),
    product_asset: serialiseAssetForStorage(state.product),
    gallery_entries: state.galleryEntries.map((entry) => ({
      id: entry.id,
      caption: entry.caption,
      asset: serialiseAssetForStorage(entry.asset),
      mode: entry.mode || 'upload',
      prompt: entry.prompt || null,
    })),
    template_id: state.templateId || DEFAULT_STAGE1.template_id,
    template_label: state.templateLabel || '',
    gallery_limit: state.galleryLimit || 4,
    gallery_label: state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery,
    gallery_allows_prompt: state.galleryAllowsPrompt !== false,
    gallery_allows_upload: state.galleryAllowsUpload !== false,
    layout_preview: layoutPreview,
    preview_built: previewBuilt,
  };
}

const FEATURE_TAG_CLASSNAMES = [
  'feature-tag feature-tag--top',
  'feature-tag feature-tag--middle',
  'feature-tag feature-tag--bottom',
];

function renderFeatureTags(target, features) {
  const container = target || document.getElementById('poster-result-feature-list');
  if (!container) return;
  const spans = container.querySelectorAll('.feature-tag span');
  const items = container.querySelectorAll('.feature-tag');
  const fallbackText = '待生成';

  spans.forEach((span, index) => {
    const nextText = features?.[index] || '';
    setTextIfNonEmpty(span, nextText, fallbackText);
    const item = items[index];
    if (item) {
      item.style.display = '';
    }
  });
}

function saveStage1Data(data, options = {}) {
  const { preserveStage2 = false } = options;
  try {
    sessionStorage.setItem(STORAGE_KEYS.stage1, JSON.stringify(data));
  } catch (error) {
    if (isQuotaError(error)) {
      console.warn('sessionStorage 容量不足，正在尝试覆盖旧的环节 1 数据。', error);
      try {
        sessionStorage.removeItem(STORAGE_KEYS.stage1);
        sessionStorage.setItem(STORAGE_KEYS.stage1, JSON.stringify(data));
      } catch (innerError) {
        console.error('无法保存环节 1 数据，已放弃持久化。', innerError);
      }
    } else {
      console.error('保存环节 1 数据失败。', error);
    }
  }
  if (!preserveStage2) {
    const stage2Raw = sessionStorage.getItem(STORAGE_KEYS.stage2);
    if (stage2Raw) {
      try {
        const stage2Meta = JSON.parse(stage2Raw);
        const key = stage2Meta?.poster_image?.storage_key;
        if (key) {
          void assetStore.delete(key);
        }
      } catch (error) {
        console.warn('清理环节 2 缓存时解析失败。', error);
      }
    }
    sessionStorage.removeItem(STORAGE_KEYS.stage2);
  }
}

function loadStage1Data() {
  const raw = sessionStorage.getItem(STORAGE_KEYS.stage1);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (error) {
    console.error('Unable to parse stage1 data', error);
    return null;
  }
}
function loadPromptPresets() {
  if (!promptPresetPromise) {
    promptPresetPromise = fetch(assetUrl(PROMPT_PRESETS_PATH))
      .then((response) => {
        if (!response.ok) {
          throw new Error('无法加载提示词预设');
        }
        return response.json();
      })
      .catch((error) => {
        promptPresetPromise = null;
        throw error;
      });
  }
  return promptPresetPromise.then((data) => ({
    presets: data?.presets || {},
    defaultAssignments: data?.defaultAssignments || {},
  }));
}

const PROMPT_SLOT_LABELS = {
  scenario: '场景背景',
  product: '核心产品',
  gallery: '底部系列小图',
};

const PROMPT_SLOT_LABELS_EN = {
  scenario: 'Scenario Background',
  product: 'Hero Product',
  gallery: 'Gallery Thumbnails',
};

function createPromptState(stage1Data, presets) {
  const state = {
    slots: {},
    seed: parseSeed(stage1Data?.prompt_seed),
    lockSeed: Boolean(stage1Data?.prompt_lock_seed),
    variants: clampVariants(Number(stage1Data?.prompt_variants) || DEFAULT_PROMPT_VARIANTS),
  };
  const savedSlots = stage1Data?.prompt_settings || {};
  const presetMap = presets.presets || {};
  const defaults = presets.defaultAssignments || {};
  PROMPT_SLOTS.forEach((slot) => {
    const saved = savedSlots?.[slot] || {};
    const fallbackId = defaults?.[slot] || Object.keys(presetMap)[0] || null;
    const presetId = saved.preset || fallbackId;
    const preset = (presetMap && presetId ? presetMap[presetId] : null) || {};
    state.slots[slot] = {
      preset: presetId,
      positive: saved.positive ?? preset.positive ?? '',
      negative: saved.negative ?? preset.negative ?? '',
      aspect: saved.aspect ?? preset.aspect ?? '',
    };
  });
  return state;
}

function clonePromptState(state) {
  return JSON.parse(JSON.stringify(state || {}));
}

function clampVariants(value) {
  const num = Number.isFinite(value) ? value : Number(value);
  if (!Number.isFinite(num)) return DEFAULT_PROMPT_VARIANTS;
  return Math.min(Math.max(Math.round(num), 1), 3);
}

function parseSeed(raw) {
  if (raw === '' || raw === null || raw === undefined) return null;
  const num = Number(raw);
  if (!Number.isFinite(num) || num < 0) return null;
  return Math.floor(num);
}

function serialisePromptState(state) {
  const payload = {};
  PROMPT_SLOTS.forEach((slot) => {
    const entry = state.slots?.[slot];
    if (!entry) return;
    payload[slot] = {
      preset: entry.preset || null,
      positive: entry.positive || '',
      negative: entry.negative || '',
      aspect: entry.aspect || '',
    };
  });
  return payload;
}

function buildPromptPreviewText(state) {
  const lines = [];
  PROMPT_SLOTS.forEach((slot) => {
    const entry = state.slots?.[slot];
    if (!entry) return;
    lines.push(`【${PROMPT_SLOT_LABELS[slot] || slot}】`);
    if (entry.positive) {
      lines.push(`正向：${entry.positive}`);
    }
    if (entry.negative) {
      lines.push(`负向：${entry.negative}`);
    }
    if (entry.aspect) {
      lines.push(`画幅：${entry.aspect}`);
    }
    lines.push('');
  });
  return lines.join('\n').trim();
}

function buildTemplateDefaultPrompt(stage1Data, templateSpec, presets) {
  if (!templateSpec) return '';

  const lines = [];
  const templateName = templateSpec.name || templateSpec.id || 'Poster Template';
  const version = templateSpec.version ? ` v${templateSpec.version}` : '';
  lines.push(`${templateName}${version}`.trim());

  const width = templateSpec.size?.width;
  const height = templateSpec.size?.height;
  if (width && height) {
    lines.push(`Canvas: ${width} × ${height} px`);
  }

  if (stage1Data?.brand_name) {
    lines.push(`Brand: ${stage1Data.brand_name}`);
  }
  if (stage1Data?.agent_name) {
    lines.push(`Distributor: ${stage1Data.agent_name}`);
  }
  if (stage1Data?.product_name) {
    lines.push(`Product: ${stage1Data.product_name}`);
  }
  if (stage1Data?.title) {
    lines.push(`Headline: ${stage1Data.title}`);
  }
  if (stage1Data?.subtitle) {
    lines.push(`Tagline: ${stage1Data.subtitle}`);
  }
  if (stage1Data?.series_description) {
    lines.push(`Series copy: ${stage1Data.series_description}`);
  }

  const features = Array.isArray(stage1Data?.features)
    ? stage1Data.features.filter(Boolean)
    : [];
  if (features.length) {
    lines.push('Feature highlights:');
    features.forEach((feature, index) => {
      lines.push(`- Feature ${index + 1}: ${feature}`);
    });
  }

  const slotMap = templateSpec.slots || {};
  const presetMap = presets?.presets || {};
  const defaults = presets?.defaultAssignments || {};

  const promptSections = [];
  PROMPT_SLOTS.forEach((slot) => {
    const slotSpec = slotMap[slot];
    if (!slotSpec) return;
    const label = PROMPT_SLOT_LABELS_EN[slot] || slot;
    const guidance = slotSpec.guidance || {};
    const presetId = guidance.preset || defaults[slot] || null;
    const preset = presetId ? presetMap[presetId] || null : null;
    const section = [];
    section.push(`- ${label}: ${presetId || 'N/A'}`);
    if (preset?.positive) {
      section.push(`  • Positive: ${preset.positive}`);
    }
    if (preset?.negative) {
      section.push(`  • Negative: ${preset.negative}`);
    }
    if (preset?.aspect || guidance.aspect) {
      section.push(`  • Aspect: ${preset?.aspect || guidance.aspect}`);
    }
    if (guidance.mode) {
      section.push(`  • Mode: ${guidance.mode}`);
    }
    promptSections.push(section.join('\n'));
  });

  if (promptSections.length) {
    lines.push('');
    lines.push('Template prompt presets:');
    lines.push(promptSections.join('\n'));
  }

  return lines.join('\n').trim();
}

function buildPromptRequest(state) {
  const prompts = {};
  PROMPT_SLOTS.forEach((slot) => {
    const entry = state.slots?.[slot];
    if (!entry) return;
    prompts[slot] = {
      preset: entry.preset || null,
      positive: entry.positive?.trim() || null,
      negative: entry.negative?.trim() || null,
      aspect: entry.aspect || null,
    };
  });
  const variants = clampVariants(state.variants || DEFAULT_PROMPT_VARIANTS);
  const seed = state.lockSeed ? parseSeed(state.seed) : null;
  return { prompts, variants, seed, lockSeed: Boolean(state.lockSeed) };
}

function applyPromptStateToInspector(state, elements, presets) {
  if (!elements) return;
  const presetMap = presets?.presets || {};
  PROMPT_SLOTS.forEach((slot) => {
    const select = elements.selects?.[slot];
    const positive = elements.positives?.[slot];
    const negative = elements.negatives?.[slot];
    const aspectLabel = elements.aspects?.[slot];
    const entry = state.slots?.[slot];
    if (select) {
      select.value = entry?.preset || '';
    }
    if (positive) {
      positive.value = entry?.positive || '';
    }
    if (negative) {
      negative.value = entry?.negative || '';
    }
    if (aspectLabel) {
      const preset = entry?.preset ? presetMap[entry.preset] : null;
      const aspect = entry?.aspect || preset?.aspect || '';
      aspectLabel.textContent = aspect ? `推荐画幅：${aspect}` : '未设置画幅约束';
    }
  });
  if (elements.seedInput) {
    elements.seedInput.value = state.seed ?? '';
    elements.seedInput.disabled = !state.lockSeed;
  }
  if (elements.lockSeedCheckbox) {
    elements.lockSeedCheckbox.checked = Boolean(state.lockSeed);
  }
  if (elements.variantsInput) {
    elements.variantsInput.value = clampVariants(state.variants || DEFAULT_PROMPT_VARIANTS);
  }
}

function populatePresetSelect(select, presets, slot) {
  if (!select) return;
  select.innerHTML = '';
  const presetMap = presets?.presets || {};
  const entries = Object.entries(presetMap);
  if (!entries.length) {
    select.disabled = true;
    const option = document.createElement('option');
    option.value = '';
    option.textContent = '暂无预设';
    select.appendChild(option);
    return;
  }
  entries.forEach(([id, config]) => {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = config?.label || `${slot}：${id}`;
    select.appendChild(option);
  });
}

function persistPromptState(stage1Data, state) {
  stage1Data.prompt_settings = serialisePromptState(state);
  stage1Data.prompt_seed = parseSeed(state.seed);
  stage1Data.prompt_lock_seed = Boolean(state.lockSeed);
  stage1Data.prompt_variants = clampVariants(state.variants || DEFAULT_PROMPT_VARIANTS);
  saveStage1Data(stage1Data, { preserveStage2: true });
}

async function setupPromptInspector(
  stage1Data,
  { promptTextarea, statusElement, onStateChange, onABTest } = {}
) {
  const container = document.getElementById('prompt-inspector');
  if (!container) return null;

  let presets;
  try {
    presets = await loadPromptPresets();
  } catch (error) {
    console.error('加载提示词预设失败', error);
    if (statusElement) {
      setStatus(statusElement, '提示词预设加载失败，将使用空白提示词。', 'warning');
    }
    presets = { presets: {}, defaultAssignments: {} };
  }

  const selects = {};
  const positives = {};
  const negatives = {};
  const aspects = {};
  const resets = {};

  PROMPT_SLOTS.forEach((slot) => {
    selects[slot] = container.querySelector(`[data-preset-select="${slot}"]`);
    positives[slot] = container.querySelector(`[data-positive="${slot}"]`);
    negatives[slot] = container.querySelector(`[data-negative="${slot}"]`);
    aspects[slot] = container.querySelector(`[data-aspect="${slot}"]`);
    resets[slot] = container.querySelector(`[data-reset="${slot}"]`);
    populatePresetSelect(selects[slot], presets, slot);
  });

  const seedInput = container.querySelector('#prompt-seed');
  const lockSeedCheckbox = container.querySelector('#prompt-lock-seed');
  const variantsInput = container.querySelector('#prompt-variants');
  const previewButton = container.querySelector('#preview-prompts');
  const abButton = container.querySelector('#generate-ab');

  const elements = {
    selects,
    positives,
    negatives,
    aspects,
    seedInput,
    lockSeedCheckbox,
    variantsInput,
  };

  const state = createPromptState(stage1Data, presets);
  applyPromptStateToInspector(state, elements, presets);

  const emitStateChange = () => {
    if (typeof onStateChange === 'function') {
      onStateChange(clonePromptState(state), presets);
    }
  };

  const persist = () => {
    persistPromptState(stage1Data, state);
    emitStateChange();
  };

  emitStateChange();

  const applyPreset = (slot, presetId) => {
    const preset = presets.presets?.[presetId] || {};
    const entry = state.slots[slot];
    entry.preset = presetId || null;
    if (preset.positive) {
      entry.positive = preset.positive;
    }
    if (preset.negative !== undefined) {
      entry.negative = preset.negative || '';
    }
    if (preset.aspect) {
      entry.aspect = preset.aspect;
    }
    applyPromptStateToInspector(state, elements, presets);
    persist();
  };

  PROMPT_SLOTS.forEach((slot) => {
    const select = selects[slot];
    const positive = positives[slot];
    const negative = negatives[slot];
    const reset = resets[slot];

    if (select) {
      select.addEventListener('change', (event) => {
        applyPreset(slot, event.target.value || null);
      });
    }

    if (positive) {
      positive.addEventListener('input', (event) => {
        state.slots[slot].positive = event.target.value;
        persist();
      });
    }

    if (negative) {
      negative.addEventListener('input', (event) => {
        state.slots[slot].negative = event.target.value;
        persist();
      });
    }

    if (reset) {
      reset.addEventListener('click', () => {
        const presetId = state.slots[slot].preset;
        if (presetId) {
          applyPreset(slot, presetId);
        } else {
          state.slots[slot].positive = '';
          state.slots[slot].negative = '';
          state.slots[slot].aspect = '';
          applyPromptStateToInspector(state, elements, presets);
          persist();
        }
      });
    }
  });

  if (lockSeedCheckbox) {
    lockSeedCheckbox.addEventListener('change', () => {
      state.lockSeed = lockSeedCheckbox.checked;
      if (!state.lockSeed) {
        state.seed = null;
      }
      applyPromptStateToInspector(state, elements, presets);
      persist();
    });
  }

  if (seedInput) {
    seedInput.addEventListener('input', (event) => {
      state.seed = parseSeed(event.target.value);
      persist();
    });
  }

  if (variantsInput) {
    variantsInput.addEventListener('change', (event) => {
      state.variants = clampVariants(Number(event.target.value) || DEFAULT_PROMPT_VARIANTS);
      applyPromptStateToInspector(state, elements, presets);
      persist();
    });
  }

  if (previewButton && promptTextarea) {
    previewButton.addEventListener('click', () => {
      promptTextarea.value = buildPromptPreviewText(state);
      setStatus(statusElement, '已根据提示词 Inspector 更新预览。', 'info');
    });
  }

  const api = {
    getState: () => clonePromptState(state),
    buildRequest: () => buildPromptRequest(state),
    setVariants(value) {
      state.variants = clampVariants(value);
      applyPromptStateToInspector(state, elements, presets);
      persist();
    },
    setSeed(value, lock) {
      if (typeof lock === 'boolean') {
        state.lockSeed = lock;
      }
      state.seed = parseSeed(value);
      applyPromptStateToInspector(state, elements, presets);
      persist();
    },
    refresh() {
      applyPromptStateToInspector(state, elements, presets);
    },
    presets,
    applyBackend(bundle) {
      if (!bundle) return;
      PROMPT_SLOTS.forEach((slot) => {
        const incoming = bundle?.[slot];
        if (!incoming) return;
        const entry = state.slots[slot];
        if (!entry) return;
        if (incoming.preset !== undefined) {
          entry.preset = incoming.preset || null;
        }
        if (incoming.positive !== undefined) {
          entry.positive = incoming.positive || '';
        }
        if (incoming.negative !== undefined) {
          entry.negative = incoming.negative || '';
        }
        if (incoming.aspect !== undefined) {
          entry.aspect = incoming.aspect || '';
        }
      });
      applyPromptStateToInspector(state, elements, presets);
      persist();
    },
  };

  if (abButton) {
    abButton.addEventListener('click', () => {
      api.setVariants(Math.max(2, state.variants || 2));
      if (typeof onABTest === 'function') {
        onABTest();
      }
    });
  }

  return api;
}

function initStage2() {
  void (async () => {
    const statusElement = document.getElementById('stage2-status');
    const layoutStructure = document.getElementById('layout-structure-text');
    const posterOutput = document.getElementById('poster-output');
    const aiPreview = document.getElementById('ai-preview');
    const aiSpinner = document.getElementById('ai-spinner');
    const aiPreviewMessage = document.getElementById('ai-preview-message');
    const posterVisual = document.getElementById('poster-visual');
    const posterTemplateImage = document.getElementById('poster-template-image');
    const posterTemplatePlaceholder = document.getElementById('poster-template-placeholder');
    const posterTemplateLink = document.getElementById('poster-template-link');
    const posterGeneratedImage = document.querySelector('[data-role="vertex-poster-img"]');
    const posterGeneratedPlaceholder = document.querySelector('[data-role="vertex-poster-placeholder"]');
    const promptGroup = document.getElementById('prompt-group');
    const promptDefaultGroup = document.getElementById('prompt-default-group');
    const promptBundleGroup = document.getElementById('prompt-bundle-group');
    const emailGroup = document.getElementById('email-group');
    const promptTextarea = document.getElementById('openai-request-prompt');
    const defaultPromptTextarea = document.getElementById('template-default-prompt');
    const promptBundlePre = document.getElementById('prompt-bundle-json');
    const emailTextarea = document.getElementById('generated-email');
    const generateButton = document.getElementById('generate-poster');
    const regenerateButton = document.getElementById('regenerate-poster');
    const nextButton = document.getElementById('to-stage3');
    const overviewList = document.getElementById('stage1-overview');
    const templateSelect = document.getElementById('template-select');
    const templateCanvas = document.getElementById('template-preview-canvas');
    const templateDescription = document.getElementById('template-description');
    const apiBaseInput = document.getElementById('api-base');
    const posterLayout = document.getElementById('posterB-layout');
    const exportPosterButton = document.getElementById('export-poster-b');

    if (!generateButton || !nextButton) {
      return;
    }

    const stage1Data = loadStage1Data();
    if (!stage1Data || !stage1Data.preview_built) {
      setStatus(statusElement, '请先完成环节 1 的素材输入与版式预览。', 'warning');
      generateButton.disabled = true;
      if (regenerateButton) {
        regenerateButton.disabled = true;
      }
      return;
    }

    await hydrateStage1DataAssets(stage1Data);

    try {
      lastStage1Data = stage1Data ? structuredClone(stage1Data) : null;
    } catch (error) {
      try {
        lastStage1Data = stage1Data ? JSON.parse(JSON.stringify(stage1Data)) : null;
      } catch {
        lastStage1Data = stage1Data || null;
      }
      console.warn('[initStage2] unable to deep copy stage1Data, using fallback reference', error);
    }

    stage2State.poster = {
      brand_name: stage1Data.brand_name || '',
      agent_name: stage1Data.agent_name || '',
      headline: stage1Data.title || '',
      tagline: stage1Data.subtitle || '',
      features: Array.isArray(stage1Data.features) ? stage1Data.features.filter(Boolean) : [],
      series: Array.isArray(stage1Data.gallery_entries)
        ? stage1Data.gallery_entries.filter(Boolean).map((entry) => ({ name: entry.caption || '' }))
        : [],
      gallery_entries: Array.isArray(stage1Data.gallery_entries)
        ? stage1Data.gallery_entries.filter(Boolean)
        : [],
    };

    stage2State.assets = {
      brand_logo_url: pickImageSrc(stage1Data.brand_logo) || '',
      scenario_url: pickImageSrc(stage1Data.scenario_asset) || '',
      product_url: pickImageSrc(stage1Data.product_asset) || '',
      gallery_urls: Array.isArray(stage1Data.gallery_entries)
        ? stage1Data.gallery_entries
            .map((entry) => pickImageSrc(entry?.asset))
            .filter(Boolean)
        : [],
      composite_poster_url: '',
    };
    stage2State.assetsB = stage2State.assetsB || {};

    renderPosterResult();

    if (posterLayout) {
      posterLayoutRoot = posterLayout;
    }
    refreshPosterLayoutPreview();

    if (exportPosterButton && posterLayout) {
      exportPosterButton.addEventListener('click', async () => {
        try {
          exportPosterButton.disabled = true;
          const html2canvas = await loadHtml2Canvas();
          if (!posterLayoutRoot || !html2canvas) return;
          const canvas = await html2canvas(posterLayoutRoot, {
            backgroundColor: '#ffffff',
            scale: 2,
          });
          const dataUrl = canvas.toDataURL('image/png');
          const link = document.createElement('a');
          link.download = 'poster-b.png';
          link.href = dataUrl;
          link.click();
        } catch (error) {
          console.error('导出预览失败', error);
          alert('导出预览失败，请稍后重试。');
        } finally {
          exportPosterButton.disabled = false;
        }
      });
    }

    let promptManager = null;
    let currentTemplateAssets = null;
    let latestPromptState = null;
    let promptPresets = null;
    let activeTemplatePoster = null;

    const templatePlaceholderDefault =
      posterTemplatePlaceholder?.textContent?.trim() || '后台尚未上传模板海报。';
    const generatedPlaceholderDefault =
      posterGeneratedPlaceholder?.textContent?.trim() || '生成结果将在此展示。';

    const templateState = {
      loaded: false,
      poster: null,
      variantA: null,
      variantB: null,
    };

    const normalisePosterRecord = (poster) => {
      if (!poster) return null;
      const source = getPosterImageSource(poster);
      if (!source) return null;
      const filename =
        typeof poster.filename === 'string' && poster.filename.trim()
          ? poster.filename.trim()
          : `${stage1Data.template_id || 'template'}-poster-a`;
      const mediaType =
        typeof poster.media_type === 'string' && poster.media_type
          ? poster.media_type
          : inferImageMediaType(source) || 'image/png';
      const width = typeof poster.width === 'number' ? poster.width : null;
      const height = typeof poster.height === 'number' ? poster.height : null;
      const normalizedUrl = HTTP_URL_RX.test(source) ? source : null;
      const normalizedDataUrl = source.startsWith('data:') ? source : null;
      return {
        filename,
        media_type: mediaType,
        width,
        height,
        key: typeof poster.key === 'string' ? poster.key : null,
        url: normalizedUrl,
        data_url:
          normalizedDataUrl ||
          (typeof poster.data_url === 'string' ? poster.data_url : null),
      };
    };

    const computeTemplatePoster = () => {
      const uploadedPoster = normalisePosterRecord(templateState.poster);
      if (uploadedPoster) {
        return uploadedPoster;
      }

      const templateImage = currentTemplateAssets?.image || null;
      const entryPreview = currentTemplateAssets?.entry?.preview || null;
      const fallbackSrc =
        templateImage?.currentSrc ||
        templateImage?.src ||
        (entryPreview
          ? App.utils.assetUrl?.(`templates/${entryPreview}`) ||
            `templates/${entryPreview}`
          : null);

      if (!fallbackSrc) {
        return null;
      }

      const width =
        typeof templateImage?.naturalWidth === 'number' && templateImage.naturalWidth > 0
          ? templateImage.naturalWidth
          : typeof templateImage?.width === 'number'
          ? templateImage.width
          : null;
      const height =
        typeof templateImage?.naturalHeight === 'number' && templateImage.naturalHeight > 0
          ? templateImage.naturalHeight
          : typeof templateImage?.height === 'number'
          ? templateImage.height
          : null;

      return {
        filename: `${stage1Data.template_id || 'template'}-poster-a`,
        media_type: inferImageMediaType(fallbackSrc) || 'image/png',
        width,
        height,
        url: fallbackSrc,
        data_url: null,
      };
    };

    const updateTemplatePosterDisplay = (message) => {
      const poster = computeTemplatePoster();
      activeTemplatePoster = poster ? { ...poster } : null;
      const displayMessage = message || templatePlaceholderDefault;
      if (
        poster &&
        posterTemplateImage &&
        assignPosterImage(
          posterTemplateImage,
          poster,
          `${stage1Data.product_name || '模板'} 默认模板海报`
        )
      ) {
        posterTemplateImage.classList.remove('hidden');
        if (posterTemplatePlaceholder) {
          posterTemplatePlaceholder.textContent = templatePlaceholderDefault;
          posterTemplatePlaceholder.classList.add('hidden');
        }
      } else {
        if (posterTemplateImage) {
          posterTemplateImage.classList.add('hidden');
          posterTemplateImage.removeAttribute('src');
        }
        if (posterTemplatePlaceholder) {
          posterTemplatePlaceholder.textContent = displayMessage;
          posterTemplatePlaceholder.classList.remove('hidden');
        }
      }
      if (posterTemplateLink) {
        const linkSrc = poster ? getPosterImageSource(poster) : null;
        if (linkSrc) {
          posterTemplateLink.href = linkSrc;
          posterTemplateLink.classList.remove('hidden');
        } else {
          posterTemplateLink.classList.add('hidden');
          posterTemplateLink.removeAttribute('href');
        }
      }
    };

    const loadTemplatePosters = async ({ silent = false, force = false } = {}) => {
      if (!force && templateState.loaded) {
        return Boolean(templateState.poster);
      }

      const candidates = getApiCandidates();
      if (!candidates.length) {
        templateState.loaded = false;
        templateState.poster = null;
        templateState.variantA = null;
        templateState.variantB = null;
        updateTemplatePosterDisplay('请先填写后端 API 地址以加载模板海报。');
        if (!silent) {
          setStatus(statusElement, '请先填写后端 API 地址以加载模板海报。', 'info');
        }
        return false;
      }

      try {
        await warmUp(candidates);
      } catch (error) {
        console.warn('模板海报 warm up 失败', error);
      }

      for (const base of candidates) {
        const url = joinBasePath(base, '/api/template-posters');
        if (!url) continue;
        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: { Accept: 'application/json' },
            mode: 'cors',
            cache: 'no-store',
            credentials: 'omit',
          });
          if (!response.ok) {
            continue;
          }
          const payload = await response.json().catch(() => ({ posters: [] }));
          const posters = Array.isArray(payload?.posters) ? payload.posters : [];
          const variantA = posters.find((item) => item?.slot === 'variant_a')?.poster || null;
          const variantB = posters.find((item) => item?.slot === 'variant_b')?.poster || null;
          templateState.poster = variantA;
          templateState.variantA = variantA;
          templateState.variantB = variantB;
          templateState.loaded = true;
          updateTemplatePosterDisplay();
          if (!silent) {
            setStatus(statusElement, '模板海报已同步。', 'success');
          }
          return Boolean(variantA);
        } catch (error) {
          console.warn('加载模板海报失败', base, error);
        }
      }

      if (!templateState.poster) {
        updateTemplatePosterDisplay('无法加载模板海报，请稍后重试。');
      }
      if (!silent) {
        setStatus(statusElement, '模板海报加载失败，请稍后重试。', 'warning');
      }
      templateState.loaded = false;
      templateState.variantA = null;
      templateState.variantB = null;
      return false;
    };

    void loadTemplatePosters({ silent: true, force: true });

    const updatePromptPanels = (options = {}) => {
      const spec = options.spec || currentTemplateAssets?.spec || null;
      const presetsSource =
        options.presets || promptPresets || promptManager?.presets || { presets: {}, defaultAssignments: {} };

      if (defaultPromptTextarea && promptDefaultGroup) {
        const englishPrompt = buildTemplateDefaultPrompt(stage1Data, spec, presetsSource);
        if (englishPrompt) {
          defaultPromptTextarea.value = englishPrompt;
          promptDefaultGroup.classList.remove('hidden');
        } else {
          defaultPromptTextarea.value = '';
          promptDefaultGroup.classList.add('hidden');
        }
      }

      if (promptBundlePre && promptBundleGroup) {
        let bundleData = options.bundle || null;
        if (!bundleData) {
          const requestPrompts = promptManager?.buildRequest?.()?.prompts || null;
          if (requestPrompts && Object.keys(requestPrompts).length) {
            bundleData = requestPrompts;
          } else if (latestPromptState?.slots) {
            bundleData = serialisePromptState(latestPromptState);
          }
        }

        let bundleText = '';
        if (bundleData) {
          if (typeof bundleData === 'string') {
            bundleText = bundleData;
          } else if (typeof bundleData === 'object') {
            const keys = Object.keys(bundleData);
            if (keys.length) {
              bundleText = JSON.stringify(bundleData, null, 2);
            }
          }
        }

        if (bundleText) {
          promptBundlePre.value = bundleText;
          promptBundleGroup.classList.remove('hidden');
        } else {
          promptBundlePre.value = '';
          promptBundleGroup.classList.add('hidden');
        }
      }
    };
    const runGeneration = (extra = {}) => {
      const currentRequest = promptManager?.buildRequest?.();
      if (currentRequest?.prompts) {
        updatePromptPanels({ bundle: currentRequest.prompts });
      } else {
        updatePromptPanels();
      }

      const execute = async () => {
        await loadTemplatePosters({ silent: true, force: true });
        updateTemplatePosterDisplay();
        const fallbackPoster = activeTemplatePoster
          ? { ...activeTemplatePoster }
          : null;
        return triggerGeneration({
          stage1Data,
          statusElement,
          layoutStructure,
          posterOutput,
          aiPreview,
          aiSpinner,
          aiPreviewMessage,
          posterVisual,
          generatedImage: posterGeneratedImage,
          templatePoster: fallbackPoster,
          generatedPlaceholder: posterGeneratedPlaceholder,
          generatedPlaceholderDefault,
          promptGroup,
          promptBundleGroup,
          promptBundlePre,
          emailGroup,
          promptTextarea,
          emailTextarea,
          generateButton,
          regenerateButton,
          nextButton,
          promptManager,
          updatePromptPanels,
          forceVariants: extra.forceVariants ?? 1,
          ...extra,
        });
      };

      return execute().catch((error) => console.error(error));
    };

    const needsTemplatePersist = !('template_id' in stage1Data);
    stage1Data.template_id = stage1Data.template_id || DEFAULT_STAGE1.template_id;
    if (needsTemplatePersist) {
      stage1Data.layout_preview = buildLayoutPreview(stage1Data);
      if (layoutStructure) {
        layoutStructure.textContent = stage1Data.layout_preview;
      }
      saveStage1Data(stage1Data);
    }
    let currentTemplateId = stage1Data.template_id;

    if (layoutStructure && stage1Data.layout_preview) {
      layoutStructure.textContent = stage1Data.layout_preview;
    }

    let templateRegistry = [];

    const handleABTest = () => {
      if (!posterGenerationState.posterUrl) {
        alert('请先点击“生成海报与文案”，成功生成一版海报后，再进行 A/B 对比。');
        return;
      }

      const templateImgEl = document.querySelector("[data-role='template-preview-image']") || null;
      const baseline = templateImgEl
        ? {
            url: templateImgEl.src,
            width:
              typeof templateImgEl.naturalWidth === 'number' && templateImgEl.naturalWidth > 0
                ? templateImgEl.naturalWidth
                : templateImgEl.width || 0,
            height:
              typeof templateImgEl.naturalHeight === 'number' && templateImgEl.naturalHeight > 0
                ? templateImgEl.naturalHeight
                : templateImgEl.height || 0,
          }
        : activeTemplatePoster
        ? {
            url: getPosterImageSource(activeTemplatePoster),
            width: activeTemplatePoster.width || 0,
            height: activeTemplatePoster.height || 0,
          }
        : null;

      const generated = {
        url: posterGenerationState.posterUrl,
        width: posterGenerationState.rawResult?.poster_image?.width || 0,
        height: posterGenerationState.rawResult?.poster_image?.height || 0,
      };

      openABModal?.(baseline, generated) ||
        alert('已准备好最新生成结果，可在右侧预览卡片查看。');
    };

    promptManager = await setupPromptInspector(stage1Data, {
      promptTextarea,
      statusElement,
      onABTest: handleABTest,
      onStateChange: (stateSnapshot, presets) => {
        latestPromptState = stateSnapshot || latestPromptState;
        if (presets) {
          promptPresets = presets;
        }
        updatePromptPanels();
      },
    });

    if (promptManager) {
      promptPresets = promptManager.presets || promptPresets;
      latestPromptState = promptManager.getState?.() || latestPromptState;
      updatePromptPanels();
    }

    const updateSummary = () => {
      const templateId = stage1Data.template_id || DEFAULT_STAGE1.template_id;
      const entry = templateRegistry.find((item) => item.id === templateId);
      const label = entry?.name || stage1Data.template_label || null;
      populateStage1Summary(stage1Data, overviewList, label);
    };

    updateSummary();

    async function refreshTemplatePreview(templateId) {
      if (!templateCanvas) return;
      try {
        const assets = await App.utils.ensureTemplateAssets(templateId);
        currentTemplateAssets = assets;
        if (templateDescription) {
          templateDescription.textContent = assets.entry?.description || '';
        }
        const previewAssets = await prepareTemplatePreviewAssets(stage1Data);
        drawTemplatePreview(templateCanvas, assets, stage1Data, previewAssets);
        updatePromptPanels({ spec: assets.spec });
        updateTemplatePosterDisplay();
      } catch (error) {
        console.error(error);
        currentTemplateAssets = null;
        updatePromptPanels();
        if (templateDescription) {
          templateDescription.textContent = '';
        }
        const ctx = templateCanvas?.getContext?.('2d');
        if (ctx && templateCanvas) {
          ctx.clearRect(0, 0, templateCanvas.width, templateCanvas.height);
          ctx.fillStyle = '#f4f5f7';
          ctx.fillRect(0, 0, templateCanvas.width, templateCanvas.height);
          ctx.fillStyle = '#6b7280';
          ctx.font = '16px "Noto Sans SC", "Microsoft YaHei", sans-serif';
          ctx.fillText('模板预览加载失败', 40, 40);
        }
        updateTemplatePosterDisplay('模板预览加载失败');
      }
    }

    if (templateSelect && templateCanvas) {
      try {
        templateRegistry = await App.utils.loadTemplateRegistry();
        templateSelect.innerHTML = '';
        templateRegistry.forEach((entry) => {
          const option = document.createElement('option');
          option.value = entry.id;
          option.textContent = entry.name;
          templateSelect.appendChild(option);
        });
        const activeEntry = templateRegistry.find((entry) => entry.id === currentTemplateId);
        if (!activeEntry && templateRegistry[0]) {
          const fallbackEntry = templateRegistry[0];
          currentTemplateId = fallbackEntry.id;
          stage1Data.template_id = fallbackEntry.id;
          stage1Data.template_label = fallbackEntry.name || '';
          stage1Data.layout_preview = buildLayoutPreview(stage1Data);
          if (layoutStructure) {
            layoutStructure.textContent = stage1Data.layout_preview;
          }
          saveStage1Data(stage1Data);
        } else if (activeEntry) {
          const label = activeEntry.name || '';
          if (stage1Data.template_label !== label) {
            stage1Data.template_label = label;
            stage1Data.layout_preview = buildLayoutPreview(stage1Data);
            if (layoutStructure) {
              layoutStructure.textContent = stage1Data.layout_preview;
            }
            saveStage1Data(stage1Data, { preserveStage2: true });
          }
        }
        templateSelect.value = currentTemplateId;
        templateSelect.disabled = true;
        templateSelect.title = '模板已在环节 1 中选定，可返回修改';
        await refreshTemplatePreview(currentTemplateId);
        updateSummary();
      } catch (error) {
        console.error(error);
        setStatus(statusElement, '模板清单加载失败，请检查 templates/ 目录。', 'warning');
      }
    }

    if (templateSelect) {
      templateSelect.addEventListener('change', async (event) => {
        const value = event.target.value || DEFAULT_STAGE1.template_id;
        currentTemplateId = value;
        stage1Data.template_id = value;
        const entry = templateRegistry.find((item) => item.id === value);
        stage1Data.template_label = entry?.name || '';
        stage1Data.layout_preview = buildLayoutPreview(stage1Data);
        if (layoutStructure) {
          layoutStructure.textContent = stage1Data.layout_preview;
        }
        saveStage1Data(stage1Data, { preserveStage2: true });
        updateSummary();
        await refreshTemplatePreview(value);
        setStatus(statusElement, '模板已切换，请重新生成海报以应用新布局。', 'info');
      });
    }

    if (apiBaseInput) {
      apiBaseInput.addEventListener('change', () => {
        templateState.loaded = false;
        templateState.poster = null;
        updateTemplatePosterDisplay('正在重新加载模板海报…');
        void loadTemplatePosters({ silent: true, force: true });
      });
    }

    generateButton.addEventListener('click', () => {
      runGeneration();
    });

    if (regenerateButton) {
      regenerateButton.addEventListener('click', () => {
        runGeneration();
      });
    }

    nextButton.addEventListener('click', async () => {
      const stored = await loadStage2Result();
      if (!stored || !stored.poster_image) {
        setStatus(statusElement, '请先完成海报生成，再前往环节 3。', 'warning');
        return;
      }
      window.location.href = 'stage3.html';
    });

    // --- A/B variant controls (Stage 2) ---
    const variantABtn = document.getElementById('variant-a-btn');
    const variantBBtn = document.getElementById('variant-b-btn');
    const abPreviewA = document.getElementById('ab-preview-A');
    const abPreviewB = document.getElementById('ab-preview-B');

    // Optional: read previous choice from sessionStorage
    let activeVariant = 'A';
    try {
      const raw = sessionStorage.getItem('marketing-poster-stage2-variants');
      if (raw) {
        const st = JSON.parse(raw);
        if (st && (st.active === 'A' || st.active === 'B')) {
          activeVariant = st.active;
        }
      }
    } catch {
      activeVariant = 'A';
    }

    function setActiveVariant(variant) {
      activeVariant = variant === 'B' ? 'B' : 'A';
      stage2State.activeVariant = activeVariant;

      // Toggle tab button styles
      if (variantABtn) {
        const isActive = activeVariant === 'A';
        variantABtn.classList.toggle('is-active', isActive);
        variantABtn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }
      if (variantBBtn) {
        const isActive = activeVariant === 'B';
        variantBBtn.classList.toggle('is-active', isActive);
        variantBBtn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }

      // Toggle preview panels (A vs B)
      if (abPreviewA) {
        abPreviewA.classList.toggle('is-active', activeVariant === 'A');
      }
      if (abPreviewB) {
        abPreviewB.classList.toggle('is-active', activeVariant === 'B');
      }

      if (activeVariant === 'B') {
        renderPosterResultB();
      }

      // Persist choice so Stage 3 knows which poster to send
      try {
        sessionStorage.setItem(
          'marketing-poster-stage2-variants',
          JSON.stringify({ active: activeVariant }),
        );
      } catch {
        // ignore
      }
    }

    if (variantABtn) {
      variantABtn.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveVariant('A');
      });
    }

    if (variantBBtn) {
      variantBBtn.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveVariant('B');
      });
    }

    // Initialise with the last active variant (default A)
    setActiveVariant(activeVariant);
  })();
}
function populateStage1Summary(stage1Data, overviewList, templateName) {
  if (!overviewList) return;
  overviewList.innerHTML = '';

  const entries = [
    [
      '模板',
      templateName || stage1Data.template_id || DEFAULT_STAGE1.template_id,
    ],
    ['品牌 / 代理', `${stage1Data.brand_name} ｜ ${stage1Data.agent_name}`],
    ['主产品名称', stage1Data.product_name],
    [
      '功能点',
      (stage1Data.features || [])
        .map((feature, index) => `${index + 1}. ${feature}`)
        .join('\n'),
    ],
    ['标题', stage1Data.title],
    ['副标题', stage1Data.subtitle],
    [
      stage1Data.gallery_label || '底部产品',
      (() => {
        const galleryLimit = stage1Data.gallery_limit || 0;
        const galleryCount =
          stage1Data.gallery_entries?.filter((entry) =>
            entry.mode === 'prompt' ? Boolean(entry.prompt) : Boolean(entry.asset)
          ).length || 0;
        if (galleryLimit > 0) {
          return `${galleryCount} / ${galleryLimit} 项素材`;
        }
        return `${galleryCount} 项素材`;
      })(),
    ],
  ];

  entries.forEach(([term, description]) => {
    const dt = document.createElement('dt');
    dt.textContent = term;
    const dd = document.createElement('dd');
    dd.textContent = description;
    overviewList.appendChild(dt);
    overviewList.appendChild(dd);
  });
}

// ……前文保持不变

function toPromptString(value) {
  if (value == null) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value.text === 'string') return value.text.trim();
  if (typeof value.prompt === 'string') return value.prompt.trim();
  if (typeof value.positive === 'string') return value.positive.trim();
  if (typeof value.preset === 'string' && typeof value.aspect === 'string') {
    const preset = value.preset.trim();
    const aspect = value.aspect.trim();
    if (preset && aspect) return `${preset} (aspect ${aspect})`;
  }
  if (typeof value.preset === 'string') return value.preset.trim();
  try {
    return JSON.stringify(value);
  } catch (error) {
    console.warn('[toPromptString] fallback stringify failed', error);
    return String(value);
  }
}

function buildPromptBundleStrings(prompts = {}) {
  return {
    scenario: toPromptString(prompts.scenario),
    product: toPromptString(prompts.product),
    gallery: toPromptString(prompts.gallery),
  };
}

function extractVertexPosterUrl(result) {
  if (!result) return null;

  if (result.poster_image && typeof result.poster_image.url === 'string') {
    const url = result.poster_image.url.trim();
    if (url) return url;
  }
  if (typeof result.poster_image === 'string') {
    const url = result.poster_image.trim();
    if (url) return url;
  }
  if (result.poster && typeof result.poster.url === 'string') {
    const url = result.poster.url.trim();
    if (url) return url;
  }
  if (typeof result.poster === 'string') {
    const url = result.poster.trim();
    if (url) return url;
  }
  if (result.image && typeof result.image.url === 'string') {
    const url = result.image.url.trim();
    if (url) return url;
  }
  if (typeof result.url === 'string' && result.url.trim()) {
    return result.url.trim();
  }
  if (typeof result.poster_url === 'string' && result.poster_url.length > 0) {
    return result.poster_url;
  }

  if (Array.isArray(result.results) && result.results.length > 0) {
    const candidate = result.results.find((entry) => entry && entry.url) || result.results[0];
    if (candidate && typeof candidate.url === 'string' && candidate.url.length > 0) {
      return candidate.url;
    }
  }

  if (Array.isArray(result.gallery_images) && result.gallery_images.length > 0) {
    const candidate =
      result.gallery_images.find((entry) => entry && entry.url) || result.gallery_images[0];
    if (candidate && typeof candidate.url === 'string' && candidate.url.length > 0) {
      return candidate.url;
    }
  }

  if (
    result.gallery_images &&
    Array.isArray(result.gallery_images.results) &&
    result.gallery_images.results.length > 0
  ) {
    const candidate =
      result.gallery_images.results.find((entry) => entry && entry.url) ||
      result.gallery_images.results[0];
    if (candidate && typeof candidate.url === 'string' && candidate.url.length > 0) {
      return candidate.url;
    }
  }

  return null;
}

function renderPosterResult() {
  const root = document.getElementById('poster-result');
  if (!root) return;

  const { poster, assets } = stage2State;

  const logoImg = document.getElementById('poster-result-brand-logo');
  if (logoImg) {
    const logoSrc = assets.brand_logo_url || '';
    if (logoSrc) {
      logoImg.src = logoSrc;
      logoImg.style.display = 'block';
    } else if (!logoImg.getAttribute('src')) {
      logoImg.style.display = 'none';
    }
  }

  const brandNameEl = document.getElementById('poster-result-brand-name');
  const agentNameEl = document.getElementById('poster-result-agent-name');
  setTextIfNonEmpty(brandNameEl, poster.brand_name, '待生成');
  setTextIfNonEmpty(agentNameEl, poster.agent_name, '待生成');

  const scenarioImg = document.getElementById('poster-result-scenario-image');
  if (scenarioImg) {
    const src = assets.scenario_url || '';
    setImageSrcIfNonEmpty(scenarioImg, src);
  }

  const productImg = document.getElementById('poster-result-product-image');
  if (productImg) {
    const src = assets.product_url || '';
    setImageSrcIfNonEmpty(productImg, src);
  }

  const featureList = document.getElementById('poster-result-feature-list');
  if (featureList) {
    renderFeatureTags(featureList, (poster.features || []).slice(0, 3));
  }

  const gallerySlots = root.querySelectorAll('.poster-gallery-slot');
  const logoFallback = assets.brand_logo_url || poster.brand_logo_url || '';
  gallerySlots.forEach((slot, index) => {
    const img = slot.querySelector('img');
    const captionEl = slot.querySelector('.slot-caption');
    const captionTitleEl = slot.querySelector('[data-gallery-caption-title]');
    const src = assets.gallery_urls?.[index] || logoFallback || '';
    if (img) setImageSrcIfNonEmpty(img, src);
    if (captionEl && !captionTitleEl) {
      const series = poster.series?.[index];
      setTextIfNonEmpty(captionEl, series && series.name ? series.name : '', '待生成');
    }
  });

  const gallerySubtitleEl = document.getElementById('poster-result-gallery-subtitle');
  const bottomSubtitleEl = document.getElementById('poster-result-tagline');
  const subheadline =
    poster?.subheadline ||
    poster?.subtitle ||
    poster?.tagline ||
    poster?.copy?.subheadline ||
    '';
  setTextIfNonEmpty(gallerySubtitleEl, subheadline, ' ');
  setTextIfNonEmpty(bottomSubtitleEl, subheadline, ' ');

  renderGalleryCaptions();
}

function renderPosterResultB() {
  const root = document.getElementById('poster-result-b');
  if (!root) return;

  const { poster, assets } = stage2State;
  const assetsB = stage2State.assetsB || {};
  const logoFallback = assets.brand_logo_url || poster.brand_logo_url || '';
  const scenarioSrc =
    assetsB.scenario_image_url ||
    assetsB.scenario_url ||
    assets.scenario_image_url ||
    assets.scenario_url ||
    '';
  const productSrc =
    assetsB.product_image_url ||
    assetsB.product_url ||
    assets.product_image_url ||
    assets.product_url ||
    '';
  const galleryUrls = Array.isArray(assetsB.gallery_urls) && assetsB.gallery_urls.length
    ? assetsB.gallery_urls
    : assets.gallery_urls || [];

  const logoImg = root.querySelector('#poster-result-brand-logo-b');
  if (logoImg) {
    const logoSrc = assetsB.brand_logo_url || assets.brand_logo_url || '';
    if (logoSrc) {
      logoImg.src = logoSrc;
      logoImg.style.display = 'block';
    } else if (!logoImg.getAttribute('src')) {
      logoImg.style.display = 'none';
    }
  }

  setTextIfNonEmpty(
    root.querySelector('#poster-result-brand-name-b'),
    poster.brand_name,
    '待生成',
  );
  setTextIfNonEmpty(
    root.querySelector('#poster-result-agent-name-b'),
    poster.agent_name,
    '待生成',
  );

  setImageSrcIfNonEmpty(root.querySelector('#poster-result-scenario-image-b'), scenarioSrc);
  setImageSrcIfNonEmpty(root.querySelector('#poster-result-product-image-b'), productSrc);

  const featureList = root.querySelector('#poster-result-feature-list-b');
  if (featureList) {
    const spans = featureList.querySelectorAll('.feature-tag span');
    const items = featureList.querySelectorAll('.feature-tag');
    spans.forEach((span, index) => {
      const nextText = poster.features?.[index] || '';
      setTextIfNonEmpty(span, nextText, '待生成');
      const item = items[index];
      if (item) item.style.display = '';
    });
  }

  const gallerySlots = root.querySelectorAll('.poster-gallery-row .poster-gallery-slot');
  const stage1Snapshot = loadStage1Data() || lastStage1Data || {};
  const entries =
    Array.isArray(poster.gallery_entries) && poster.gallery_entries.length
      ? poster.gallery_entries
      : Array.isArray(stage1Snapshot.gallery_entries)
      ? stage1Snapshot.gallery_entries
      : [];
  const seriesFallback = Array.isArray(poster.series) ? poster.series : [];

  gallerySlots.forEach((slot, index) => {
    const img = slot.querySelector('img');
    const src = galleryUrls?.[index] || logoFallback || '';
    if (img) setImageSrcIfNonEmpty(img, src);

    const entry = entries[index] || {};
    const captionValue = entry?.caption || entry?.name || '';
    const title =
      entry?.title ||
      (entry?.caption && entry.caption.title) ||
      (typeof captionValue === 'string' ? captionValue : '') ||
      seriesFallback[index]?.name ||
      '';
    const subtitle =
      entry?.subtitle ||
      (entry?.caption && entry.caption.subtitle) ||
      '';

    setTextIfNonEmpty(
      slot.querySelector('[data-gallery-caption-title]'),
      title,
      '待生成',
    );
    setTextIfNonEmpty(
      slot.querySelector('[data-gallery-caption-subtitle]'),
      subtitle,
      '待生成',
    );
  });

  const subheadline =
    poster?.subheadline ||
    poster?.subtitle ||
    poster?.tagline ||
    poster?.copy?.subheadline ||
    '';
  setTextIfNonEmpty(root.querySelector('#poster-result-gallery-subtitle-b'), subheadline, ' ');
  setTextIfNonEmpty(root.querySelector('#poster-result-tagline-b'), subheadline, ' ');
}

function renderGalleryCaptions() {
  const root = document.getElementById('poster-result');
  if (!root) return;
  const slots = root.querySelectorAll('.poster-gallery-slot');
  if (!slots.length) return;

  const poster = stage2State.poster || {};
  const stage1Snapshot = loadStage1Data() || lastStage1Data || {};
  const entries =
    Array.isArray(poster.gallery_entries) && poster.gallery_entries.length
      ? poster.gallery_entries
      : Array.isArray(stage1Snapshot.gallery_entries)
      ? stage1Snapshot.gallery_entries
      : [];
  const seriesFallback = Array.isArray(poster.series) ? poster.series : [];

  slots.forEach((slot, index) => {
    const entry = entries[index] || {};
    const captionValue = entry?.caption || entry?.name || '';
    const title =
      entry?.title ||
      (entry?.caption && entry.caption.title) ||
      (typeof captionValue === 'string' ? captionValue : '') ||
      seriesFallback[index]?.name ||
      '';
    const subtitle =
      entry?.subtitle ||
      (entry?.caption && entry.caption.subtitle) ||
      '';

    const titleEl = slot.querySelector('[data-gallery-caption-title]');
    const subtitleEl = slot.querySelector('[data-gallery-caption-subtitle]');
    const fallbackText = '待生成';

    if (titleEl) {
      setTextIfNonEmpty(titleEl, title, fallbackText);
    }
    if (subtitleEl) {
      setTextIfNonEmpty(subtitleEl, subtitle, fallbackText);
    }
  });
}

function applyImagesToAssetsB(resp) {
  stage2State.assetsB = stage2State.assetsB || {};
  const scenarioUrl =
    resp?.scenario_image?.url ||
    resp?.scenario_image_url ||
    resp?.images?.scenario ||
    '';
  const productUrl =
    resp?.product_image?.url ||
    resp?.product_image_url ||
    resp?.images?.product ||
    '';

  if (scenarioUrl) stage2State.assetsB.scenario_image_url = scenarioUrl;
  if (productUrl) stage2State.assetsB.product_image_url = productUrl;
}

function applyVertexPosterResult(data) {
  console.log('[triggerGeneration] applyVertexPosterResult', data);

  const slotSummary = summariseGenerationSlots(data);
  console.info('[triggerGeneration] slot assets', slotSummary);

  surfaceSlotWarnings(slotSummary);

  const activeVariant = stage2State.activeVariant || stage2State.variant || 'A';
  const isA = activeVariant === 'A';
  const isB = activeVariant === 'B';

  stage2State.vertex.lastResponse = data || null;
  const assets = stage2State.assets;
  const assetsB = stage2State.assetsB || (stage2State.assetsB = {});

  if (isB && DEMO_B_AI_IMAGES_TO_ASSETSB) {
    applyImagesToAssetsB(data);
  } else if (!(isA && DEMO_A_NO_AI_IMAGES)) {
    if (data?.scenario_image?.url) {
      assets.scenario_url = data.scenario_image.url;
    }
    if (data?.product_image?.url) {
      assets.product_url = data.product_image.url;
    }
    if (Array.isArray(data?.gallery_images)) {
      assets.gallery_urls = data.gallery_images
        .map((entry) => pickImageSrc(entry))
        .filter(Boolean);
    }
  }

  const posterUrl = extractVertexPosterUrl(data);
  if (posterUrl) {
    posterGeneratedImageUrl = posterUrl;
    posterGenerationState.posterUrl = posterUrl;
    posterGeneratedImage = posterGenerationState.posterUrl;
    if (!(isB && DEMO_B_AI_IMAGES_TO_ASSETSB) && !(isA && DEMO_A_NO_AI_IMAGES)) {
      assets.composite_poster_url = posterUrl;
    }
    if (isB && DEMO_B_AI_IMAGES_TO_ASSETSB) {
      assetsB.composite_poster_url = posterUrl;
    }
    try {
      sessionStorage.setItem('latestPosterUrl', posterUrl);
    } catch (error) {
      console.warn('无法缓存最新海报 URL', error);
    }
  }

  renderPosterResult();
  renderPosterResultB();
  // --- Bind composite poster (B variant) into B preview ---
  if (!(isB && DEMO_B_AI_IMAGES_TO_ASSETSB)) {
    try {
      const vertexPosterImg = document.getElementById('vertex-poster-preview-img');
      const vertexPosterPlaceholder = document.getElementById('vertex-poster-placeholder');
      const vertexPosterUrlInput = document.getElementById('vertex-poster-url');

      if (posterUrl && vertexPosterImg) {
        vertexPosterImg.src = posterUrl;
        vertexPosterImg.style.display = 'block';
        vertexPosterImg.classList.remove('hidden');

        if (vertexPosterPlaceholder) {
          vertexPosterPlaceholder.classList.add('hidden');
        }

        if (vertexPosterUrlInput) {
          vertexPosterUrlInput.value = posterUrl;
        }
      }
    } catch (err) {
      console.warn('[applyVertexPosterResult] failed to apply B variant image', err);
    }
  } else {
    try {
      const vertexPosterImg = document.getElementById('vertex-poster-preview-img');
      const vertexPosterPlaceholder = document.getElementById('vertex-poster-placeholder');
      const vertexPosterUrlInput = document.getElementById('vertex-poster-url');
      if (vertexPosterImg) {
        vertexPosterImg.classList.add('hidden');
        vertexPosterImg.style.display = 'none';
        vertexPosterImg.removeAttribute('src');
      }
      if (vertexPosterPlaceholder) {
        vertexPosterPlaceholder.classList.add('hidden');
      }
      if (vertexPosterUrlInput) {
        vertexPosterUrlInput.value = '';
      }
    } catch (err) {
      console.warn('[applyVertexPosterResult] failed to hide composite preview', err);
    }
  }

  // --- Show poster area and reset active tab to A ---
  try {
    const posterOutput = document.getElementById('poster-output');
    const aiPreview = document.getElementById('ai-preview');
    const posterVisual = document.getElementById('poster-visual');

    if (!posterOutput || !aiPreview || !posterVisual) {
      console.warn('[applyVertexPosterResult] poster containers missing', {
        posterOutput,
        aiPreview,
        posterVisual,
      });
    } else {
      posterOutput.classList.remove('hidden');
      posterVisual.classList.remove('hidden');
      aiPreview.classList.add('hidden');
    }

    // Use the same session key as initStage2, but force back to A after a successful generation
    try {
      sessionStorage.setItem(
        'marketing-poster-stage2-variants',
        JSON.stringify({ active: 'A' }),
      );
    } catch {
      // ignore
    }

    // If the A/B buttons are already wired, we can reuse the click event to update UI
    const variantABtn = document.getElementById('variant-a-btn');
    if (variantABtn) {
      variantABtn.click();
    }
  } catch (e) {
    console.warn('[applyVertexPosterResult] show poster failed', e);
  }
}

async function buildGalleryItemsWithFallback(stage1, logoRef, apiCandidates, maxSlots = 4) {
  const result = [];
  const entries = Array.isArray(stage1?.gallery_entries)
    ? stage1.gallery_entries.filter(Boolean)
    : [];

  for (let i = 0; i < maxSlots; i += 1) {
    const entry = entries[i] || null;
    const caption = entry?.caption?.trim() || `Series ${i + 1}`;
    const promptText = entry?.prompt?.trim() || null;
    const mode = entry?.mode || 'upload';
    const normalisedMode = mode === 'logo' || mode === 'logo_fallback' ? 'upload' : mode;

    const hasPrompt = !!promptText;
    if (normalisedMode === 'prompt' && hasPrompt) {
      result.push({
        caption,
        key: null,
        asset: null,
        mode: 'prompt',
        prompt: promptText,
      });
      continue;
    }

    let ref = null;
    if (entry && entry.asset) {
      ref = await normaliseAssetReference(entry.asset, {
        field: `poster.gallery_items[${i}]`,
        required: false,
        apiCandidates,
        folder: 'gallery',
      }, logoRef);
    }

    if (ref && (ref.key || ref.url)) {
      result.push({
        caption,
        key: ref.key || null,
        asset: ref.url || null,
        mode: normalisedMode,
        prompt: promptText,
      });
      continue;
    }

    if (logoRef && (logoRef.url || logoRef.key)) {
      console.info('[triggerGeneration] gallery empty, fallback to brand logo', { index: i, caption });
      result.push({
        caption,
        key: logoRef.key || null,
        asset: logoRef.url || null,
        mode: 'upload',
        prompt: null,
      });
      continue;
    }

    console.warn('[triggerGeneration] gallery empty and no brand logo available, skip slot', { index: i, caption });
  }

  return result;
}

function formatPosterGenerationError(error) {
  const rawDetail = error?.responseJson?.detail ?? error?.responseJson ?? null;

  if (Array.isArray(rawDetail)) {
    const first = rawDetail.find((entry) => entry?.msg || entry?.message);
    if (first?.msg) return first.msg;
    if (first?.message) return first.message;
  }

  if (rawDetail && typeof rawDetail === 'object') {
    if (typeof rawDetail.message === 'string') return rawDetail.message;
    if (typeof rawDetail.error === 'string') return rawDetail.error;
  }

  if (typeof rawDetail === 'string') {
    return rawDetail;
  }

  return error?.message || '生成失败';
}

// ------- 直接替换：triggerGeneration 主流程（含双形态自适应） -------
async function triggerGeneration(opts) {
  const {
    stage1Data, statusElement,
    posterOutput, aiPreview, aiSpinner, aiPreviewMessage,
    posterVisual,
    generatedImage = null,
    generatedPlaceholder,
    generatedPlaceholderDefault = '生成结果将在此展示。',
    templatePoster = null,
    promptBundleGroup,
    promptBundlePre,
    promptGroup, emailGroup, promptTextarea, emailTextarea,
    generateButton, regenerateButton, nextButton,
    promptManager, updatePromptPanels,
    forceVariants = null, abTest = false,
  } = opts;
  rehydrateStage2PosterFromStage1();
  const activeVariant = stage2State.activeVariant || stage2State.variant || 'A';
  const isA = activeVariant === 'A';
  const isB = activeVariant === 'B';
  if (stage2InFlight) {
    setStatus(statusElement, '生成中，请稍候…', 'info');
    return null;
  }
  const mySeq = ++stage2GenerationSeq;
  stage2InFlight = true;
  setStage2ButtonsDisabled(true);
  

  // 1) 选可用 API 基址
  const apiCandidates = getApiCandidates(document.getElementById('api-base')?.value || null);
  if (!apiCandidates.length) {
    stage2InFlight = false;
    setStage2ButtonsDisabled(false);
    setStatus(statusElement, '未找到可用后端，请先填写 API 基址。', 'warning');
    return null;
  }

  // 2) 资产“再水化”确保 dataUrl 就绪（仅用于画布预览；发送给后端使用 r2Key）
  await hydrateStage1DataAssets(stage1Data);

  // 3) 主体 poster（素材必须已上云，仅传 URL/Key）
  const templateId = stage1Data.template_id;
  const sc = stage1Data.scenario_asset || null;
  const pd = stage1Data.product_asset || null;

  const scenarioMode = stage1Data.scenario_mode || 'upload';
  const productMode = stage1Data.product_mode || 'upload';

  let posterPayload;
  let brandLogoRef;
  let scenarioRef;
  let productRef;
  let galleryItems;
  try {
    brandLogoRef = await normaliseAssetReference(stage1Data.brand_logo, {
      field: 'poster.brand_logo',
      required: true,
      apiCandidates,
      folder: 'brand-logo',
    });

    scenarioRef = await normaliseAssetReference(sc, {
      field: 'poster.scenario_image',
      required: true,
      apiCandidates,
      folder: 'scenario',
    }, brandLogoRef);

    productRef = await normaliseAssetReference(pd, {
      field: 'poster.product_image',
      required: true,
      apiCandidates,
      folder: 'product',
    }, brandLogoRef);

    galleryItems = await buildGalleryItemsWithFallback(stage1Data, brandLogoRef, apiCandidates, 4);

    const features = Array.isArray(stage1Data.features)
      ? stage1Data.features.filter(Boolean)
      : [];

    const brandLogoUrl = brandLogoRef.url || null;
    const scenarioUrl = scenarioRef.url || null;
    const productUrl = productRef.url || null;

    if (scenarioUrl) {
      assertAssetUrl('场景图', scenarioUrl);
    }
    if (productUrl) {
      assertAssetUrl('主产品图', productUrl);
    }
    if (brandLogoUrl) {
      assertAssetUrl('品牌 Logo', brandLogoUrl);
    }

    posterPayload = {
      brand_name: stage1Data.brand_name,
      agent_name: stage1Data.agent_name,
      scenario_image: scenarioUrl,
      product_name: stage1Data.product_name,
      template_id: templateId,
      features,
      title: stage1Data.title,
      subtitle: stage1Data.subtitle,
      series_description: stage1Data.series_description,

      brand_logo: brandLogoUrl,
      brand_logo_key: brandLogoRef.key,

      scenario_key: scenarioRef.key,
      scenario_asset: scenarioUrl,

      product_key: productRef.key,
      product_asset: productUrl,

      scenario_mode: scenarioMode,
      scenario_prompt:
        scenarioMode === 'prompt'
          ? stage1Data.scenario_prompt || stage1Data.scenario_image || null
          : null,
      product_mode: productMode,
      product_prompt: productMode === 'prompt' ? stage1Data.product_prompt || null : null,

      gallery_items: galleryItems,
      gallery_label: stage1Data.gallery_label || null,
      gallery_limit: stage1Data.gallery_limit ?? null,
      gallery_allows_prompt: stage1Data.gallery_allows_prompt !== false,
      gallery_allows_upload: stage1Data.gallery_allows_upload !== false,
    };
  } catch (error) {
    console.error('[triggerGeneration] asset normalisation failed', error);
    setStatus(
      statusElement,
      error instanceof Error ? error.message : '素材未完成上传，请先上传至 R2/GCS。',
      'error',
    );
    stage2InFlight = false;
    setStage2ButtonsDisabled(false);
    return null;
  }
  

 // 4) Prompt 组装 —— 始终发送字符串 prompt_bundle
  const reqFromInspector = promptManager?.buildRequest?.() || {};
  if (forceVariants != null) reqFromInspector.variants = forceVariants;
  
  const promptBundleStrings = buildPromptBundleStrings(reqFromInspector.prompts || {});
  
  const requestBase = {
    poster: posterPayload,
    render_mode: 'locked',
    variants: clampVariants(reqFromInspector.variants ?? 1),
    seed: reqFromInspector.seed ?? null,
    lock_seed: !!reqFromInspector.lockSeed,
  };
  
  const payload = { ...requestBase, prompt_bundle: promptBundleStrings };
  if (isA && DEMO_A_NO_AI_IMAGES) {
    payload.generate_images = false;
    payload.generate_text = true;
  }

  const negativeSummary = summariseNegativePrompts(reqFromInspector.prompts);
  if (negativeSummary) {
    payload.negatives = negativeSummary;
  }

  if (abTest) {
    payload.variants = Math.max(2, payload.variants || 2);
  }

  const posterSummary = {
    template_id: posterPayload.template_id,
    scenario_mode: posterPayload.scenario_mode,
    product_mode: posterPayload.product_mode,
    feature_count: Array.isArray(posterPayload.features) ? posterPayload.features.length : 0,
    gallery_count: Array.isArray(posterPayload.gallery_items) ? posterPayload.gallery_items.length : 0,
  };
  const assetAudit = {
    brand_logo: {
      key: brandLogoRef?.key || null,
      url: posterPayload.brand_logo || null,
    },
    scenario: {
      mode: posterPayload.scenario_mode,
      key: posterPayload.scenario_key || null,
      url: posterPayload.scenario_asset || null,
    },
    product: {
      mode: posterPayload.product_mode,
      key: posterPayload.product_key || null,
      url: posterPayload.product_asset || null,
    },
    gallery: posterPayload.gallery_items.map((item, index) => ({
      index,
      mode: item.mode,
      key: item.key || null,
      url: item.asset || null,
    })),
  };

  console.info('[triggerGeneration] prepared payload', {
    apiCandidates,
    poster: posterSummary,
    prompt_bundle: payload.prompt_bundle,
    variants: payload.variants,
    seed: payload.seed,
    lock_seed: payload.lock_seed,
    negatives: negativeSummary || null,
  });
  console.info('[triggerGeneration] asset audit', assetAudit);
  
  // 面板同步
  updatePromptPanels?.({ bundle: payload.prompt_bundle });
  
  // 5) 体积守护
  const rawPayload = JSON.stringify(payload);
  try { validatePayloadSize(rawPayload); } catch (e) {
    setStatus(statusElement, e.message, 'error');
    stage2InFlight = false;
    setStage2ButtonsDisabled(false);
    return null;
  }
  
  // 6) UI 状态
  generateButton.disabled = true;
  if (regenerateButton) regenerateButton.disabled = true;
  setStatus(statusElement, abTest ? '正在进行 A/B 提示词生成…' : '正在生成海报与文案…', 'info');
  posterOutput?.classList.remove('hidden');
  if (aiPreview) aiPreview.classList.remove('complete');
  if (aiSpinner) aiSpinner.classList.remove('hidden');
  if (aiPreviewMessage) aiPreviewMessage.textContent = 'Glibatree Art Designer 正在绘制海报…';
  if (posterVisual) posterVisual.classList.remove('hidden');
  posterGenerationState.posterUrl = null;
  posterGeneratedImage = null;
  posterGeneratedLayout = TEMPLATE_DUAL_LAYOUT;
  const resetGeneratedPlaceholder = (message) => {
    if (!generatedPlaceholder) return;
    generatedPlaceholder.textContent = message || generatedPlaceholderDefault;
    generatedPlaceholder.classList.remove('hidden');
  };
  const hideGeneratedPlaceholder = () => {
    if (!generatedPlaceholder) return;
    generatedPlaceholder.textContent = generatedPlaceholderDefault;
    generatedPlaceholder.classList.add('hidden');
  };
  if (generatedImage?.classList) {
    generatedImage.classList.add('hidden');
    generatedImage.removeAttribute('src');
    generatedImage.style.display = 'none';
  }
  resetGeneratedPlaceholder('Glibatree Art Designer 正在绘制海报…');
  if (promptGroup) promptGroup.classList.add('hidden');
  if (emailGroup) emailGroup.classList.add('hidden');
  if (nextButton) nextButton.disabled = true;

  let fallbackTriggered = false;
  let fallbackTimerId = null;

  const clearFallbackTimer = () => {
    if (fallbackTimerId) {
      clearTimeout(fallbackTimerId);
      fallbackTimerId = null;
    }
  };

  const enableTemplateFallback = async (message, options = {}) => {
    if (fallbackTriggered) return;
    fallbackTriggered = true;
    clearFallbackTimer();
    if (aiSpinner) aiSpinner.classList.add('hidden');
    if (aiPreview) aiPreview.classList.add('complete');
    if (generatedImage?.classList) {
      generatedImage.classList.add('hidden');
      generatedImage.removeAttribute('src');
    }
    resetGeneratedPlaceholder('AI 生成超时，已回退到模板海报。');
    if (nextButton) nextButton.disabled = false;
    generateButton.disabled = false;
    if (regenerateButton) regenerateButton.disabled = false;
    if (templatePoster) {
      try {
        await saveStage2Result({
          poster_image: { ...templatePoster },
          prompt: typeof options.prompt === 'string' ? options.prompt : '',
          email_body: typeof options.email === 'string' ? options.email : '',
          variants: [],
          seed: null,
          lock_seed: false,
          template_fallback: true,
          template_id: stage1Data.template_id || null,
        });
      } catch (error) {
        console.error('保存模板海报失败', error);
      }
    }
    const statusLevel = templatePoster ? 'warning' : 'error';
    const statusMessage =
      message ||
      (templatePoster
        ? 'AI 生成超时，已回退到模板海报，可前往环节 3。'
        : 'AI 生成超时，且没有可用的模板海报。');
    setStatus(statusElement, statusMessage, statusLevel);
  };

  if (templatePoster) {
    fallbackTimerId = setTimeout(() => {
      void enableTemplateFallback();
    }, 60_000);
  }

  // 7) 发送（健康探测 + 重试）
  try {
    await warmUp(apiCandidates);
    // 发送请求：兼容返回 Response 或 JSON
    const resp = await postJsonWithRetry(apiCandidates, '/api/generate-poster', payload, 1, rawPayload);
    const data = (resp && typeof resp.json === 'function') ? await resp.json() : resp;
    if (mySeq !== stage2GenerationSeq) return null;

    const posterUrl =
      data?.poster?.asset_url ||
      data?.poster?.url ||
      data?.poster_url ||
      data?.poster_image?.url ||
      (Array.isArray(data?.results) && data.results[0]?.url) ||
      null;

    lastPosterResult = data || null;
    lastPromptBundle = data?.prompt_bundle || null;
    posterGeneratedImageUrl = posterUrl || null;

    posterGenerationState.posterUrl = posterUrl;
    posterGenerationState.promptBundle = data?.prompt_bundle || null;
    posterGenerationState.rawResult = data || null;
    posterGeneratedImage = posterGenerationState.posterUrl;
    posterGeneratedLayout = TEMPLATE_DUAL_LAYOUT;

    if (promptBundlePre && promptBundleGroup) {
      const bundle = lastPromptBundle;
      const hasBundle =
        bundle &&
        ((typeof bundle === 'string' && bundle.trim()) ||
          (typeof bundle === 'object' && Object.keys(bundle).length));
      if (hasBundle) {
        const text = typeof bundle === 'string' ? bundle : JSON.stringify(bundle, null, 2);
        promptBundlePre.value = text;
        promptBundleGroup.classList.remove('hidden');
      } else {
        promptBundlePre.value = '';
        promptBundleGroup.classList.add('hidden');
      }
    }

    console.info('[triggerGeneration] success', {
      hasPoster: Boolean(data?.poster_image),
      variants: Array.isArray(data?.variants) ? data.variants.length : 0,
      seed: data?.seed ?? null,
      lock_seed: data?.lock_seed ?? null,
    });

    applyVertexPosterResult(data);

    clearFallbackTimer();

    let assigned = false;
    if (posterGenerationState.posterUrl && generatedImage?.classList) {
      generatedImage.src = posterGenerationState.posterUrl;
      generatedImage.style.display = 'block';
      generatedImage.classList.remove('hidden');
      hideGeneratedPlaceholder();
      assigned = true;
    } else {
      if (generatedImage?.classList) {
        generatedImage.classList.add('hidden');
        generatedImage.removeAttribute('src');
        generatedImage.style.display = 'none';
      }
      resetGeneratedPlaceholder('生成结果缺少可预览图片。');
    }

    posterVisual && posterVisual.classList.remove('hidden');
    if (aiPreview) aiPreview.classList.add('complete');
    if (aiSpinner) aiSpinner.classList.add('hidden');

    if (emailTextarea) emailTextarea.value = data.email_body || '';
    if (promptTextarea) promptTextarea.value = data.prompt || '';

    if (assigned) {
      setStatus(statusElement, '生成完成', 'success');
      if (nextButton) nextButton.disabled = false;
      generateButton.disabled = false;
      if (regenerateButton) regenerateButton.disabled = false;
      try {
        const dataToStore = {
          ...data,
          template_poster: templatePoster ? { ...templatePoster } : null,
        };
        await saveStage2Result(dataToStore);
      } catch (error) {
        console.error('保存环节 2 结果失败。', error);
      }
    } else if (templatePoster) {
      await enableTemplateFallback('生成结果缺少可预览图片，已回退到模板海报，可直接前往环节 3。', {
        prompt: data?.prompt || '',
        email: data?.email_body || '',
      });
    } else {
      setStatus(statusElement, '生成完成但缺少可预览图片，请稍后重试。', 'warning');
    }

    return data;
  } catch (error) {
    console.error('[generatePoster] 请求失败', {
      error,
      status: error?.status,
      responseJson: error?.responseJson,
      responseText: error?.responseText,
    });
    posterGenerationState.posterUrl = null;
    posterGenerationState.promptBundle = null;
    posterGenerationState.rawResult = null;
    lastPosterResult = null;
    lastPromptBundle = null;
    posterGeneratedImageUrl = null;
    posterGeneratedImage = null;
    posterGeneratedLayout = TEMPLATE_DUAL_LAYOUT;
    const detail = error?.responseJson?.detail || null;
    const quotaExceeded =
      error?.status === 429 &&
      (detail?.error === 'vertex_quota_exceeded' || detail === 'vertex_quota_exceeded');
    const friendlyMessage = quotaExceeded
      ? '图像生成配额已用尽，请稍后再试，或先上传现有素材。'
      : formatPosterGenerationError(error);
    const statusHint = typeof error?.status === 'number' ? ` (HTTP ${error.status})` : '';
    const decoratedMessage = `${friendlyMessage}${statusHint}`;
    setStatus(statusElement, decoratedMessage, 'error');
    generateButton.disabled = false;
    if (regenerateButton) regenerateButton.disabled = false;
    if (aiSpinner) aiSpinner.classList.add('hidden');
    if (aiPreview) aiPreview.classList.add('complete');
    if (generatedImage?.classList) {
      generatedImage.classList.add('hidden');
      generatedImage.removeAttribute('src');
    }
    resetGeneratedPlaceholder(decoratedMessage || generatedPlaceholderDefault);
    refreshPosterLayoutPreview();
    return null;
  } finally {
    stage2InFlight = false;
    setStage2ButtonsDisabled(false);
  }
}

async function prepareTemplatePreviewAssets(stage1Data) {
  const result = {
    brand_logo: null,
    scenario: null,
    product: null,
    gallery: [],
  };

  const pickSrc = (value, depth = 0) => {
    if (!value || depth > 3) return null;
    if (typeof value === 'string') return value;

    const directFields = [
      value.dataUrl,
      value.data_url,
      value.url,
      value.remoteUrl,
      value.publicUrl,
      value.public_url,
      value.asset_url,
      value.cdnUrl,
      value.src,
    ];
    for (const field of directFields) {
      if (typeof field === 'string' && field) return field;
    }

    const nested = [value.asset, value.image, value.poster_image];
    for (const candidate of nested) {
      const picked = pickSrc(candidate, depth + 1);
      if (picked) return picked;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        const picked = pickSrc(item, depth + 1);
        if (picked) return picked;
      }
    }

    return null;
  };

  const tasks = [];
  const queue = (key, src, index) => {
    if (!src) return;
    tasks.push(
      loadImageAsset(src)
        .then((image) => {
          if (key === 'gallery') {
            result.gallery[index] = image;
          } else {
            result[key] = image;
          }
        })
        .catch(() => undefined)
    );
  };

  queue('brand_logo', pickSrc(stage1Data.brand_logo));
  queue('scenario', pickSrc(stage1Data.scenario_asset));
  queue('product', pickSrc(stage1Data.product_asset));
  (stage1Data.gallery_entries || []).forEach((entry, index) => {
    queue('gallery', pickSrc(entry?.asset || entry), index);
  });

  await Promise.allSettled(tasks);

  const galleryLimit = Math.max(
    Number(stage1Data.gallery_limit) || 0,
    (stage1Data.gallery_entries || []).length,
    4
  );
  if (result.brand_logo) {
    for (let i = 0; i < galleryLimit; i += 1) {
      if (!result.gallery[i]) {
        result.gallery[i] = result.brand_logo;
      }
    }
  }

  return result;
}

function drawTemplatePreview(canvas, assets, stage1Data, previewAssets) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const spec = assets.spec || {};
  const size = spec.size || {};
  const width = Number(size.width) || assets.image.width;
  const height = Number(size.height) || assets.image.height;

  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#f4f5f7';
  ctx.fillRect(0, 0, width, height);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(assets.image, 0, 0, width, height);

  const slots = spec.slots || {};
  const fonts = {
    brand: '600 36px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    agent: '600 30px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    title: '700 64px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    subtitle: '700 40px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    body: '400 28px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    feature: '500 26px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    caption: '400 22px "Noto Sans SC", "Microsoft YaHei", sans-serif',
  };

  const brandSlot = getSlotRect(slots.logo);
  if (brandSlot) {
    if (previewAssets.brand_logo) {
      drawPreviewImage(ctx, previewAssets.brand_logo, brandSlot, 'contain');
    } else {
      drawPreviewPlaceholder(ctx, brandSlot, stage1Data.brand_name || '品牌 Logo');
    }
  }

  const brandNameSlot = getSlotRect(slots.brand_name);
  if (brandNameSlot) {
    drawPreviewText(ctx, stage1Data.brand_name || '品牌名称', brandNameSlot, {
      font: fonts.brand,
      color: '#1f2933',
    });
  }

  const agentSlot = getSlotRect(slots.agent_name);
  if (agentSlot) {
    drawPreviewText(ctx, (stage1Data.agent_name || '代理名').toUpperCase(), agentSlot, {
      font: fonts.agent,
      color: '#1f2933',
      align: 'right',
    });
  }

  const scenarioSlot = getSlotRect(slots.scenario);
  if (scenarioSlot) {
    if (previewAssets.scenario) {
      drawPreviewImage(ctx, previewAssets.scenario, scenarioSlot, 'cover');
    } else {
      drawPreviewPlaceholder(ctx, scenarioSlot, stage1Data.scenario_image || '应用场景');
    }
  }

  const productSlot = getSlotRect(slots.product);
  if (productSlot) {
    if (previewAssets.product) {
      drawPreviewImage(ctx, previewAssets.product, productSlot, 'contain');
    } else {
      drawPreviewPlaceholder(ctx, productSlot, stage1Data.product_name || '产品渲染图');
    }
  }

  const titleSlot = getSlotRect(slots.title);
  if (titleSlot) {
    drawPreviewText(ctx, stage1Data.title || '标题文案待补充', titleSlot, {
      font: fonts.title,
      color: '#ef4c54',
      align: 'center',
      lineHeight: 72,
    });
  }

  const subtitleSlot = getSlotRect(slots.subtitle);
  if (subtitleSlot) {
    drawPreviewText(ctx, stage1Data.subtitle || '副标题待补充', subtitleSlot, {
      font: fonts.subtitle,
      color: '#ef4c54',
      align: 'right',
      lineHeight: 48,
    });
  }

  const callouts = spec.feature_callouts || [];
  callouts.forEach((callout, index) => {
    if (!stage1Data.features || !stage1Data.features[index]) return;
    const labelSlot = getSlotRect(callout.label_box);
    if (!labelSlot) return;
    drawPreviewText(
      ctx,
      `${index + 1}. ${stage1Data.features[index]}`,
      labelSlot,
      {
        font: fonts.feature,
        color: '#1f2933',
        lineHeight: 34,
      }
    );
  });

  const gallery = spec.gallery || {};
  const galleryItems = gallery.items || [];
  galleryItems.forEach((slot, index) => {
    const rect = getSlotRect(slot);
    if (!rect) return;
    const image = previewAssets.gallery[index];
    if (image) {
      ctx.save();
      ctx.filter = 'grayscale(100%)';
      drawPreviewImage(ctx, image, rect, 'cover');
      ctx.restore();
    } else {
      drawPreviewPlaceholder(ctx, rect, `底部小图 ${index + 1}`);
    }

    const caption = stage1Data.gallery_entries?.[index]?.caption;
    if (caption) {
      drawPreviewText(ctx, caption, {
        x: rect.x + 8,
        y: rect.y + rect.height - 44,
        width: rect.width - 16,
        height: 40,
      }, {
        font: fonts.caption,
        color: '#1f2933',
        lineHeight: 26,
      });
    }
  });

  const stripSlot = getSlotRect(gallery.strip);
  if (stripSlot) {
    drawPreviewText(ctx, stage1Data.series_description || '系列说明待补充', {
      x: stripSlot.x + 12,
      y: stripSlot.y + Math.max(stripSlot.height - 44, 0),
      width: stripSlot.width - 24,
      height: 40,
    }, {
      font: fonts.caption,
      color: '#1f2933',
      lineHeight: 24,
    });
  }
}

function loadImageAsset(src) {
  return new Promise((resolve, reject) => {
    const attempt = (url, allowFallback) => {
      const img = new Image();
      img.decoding = 'async';
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = async () => {
        if (!allowFallback) {
          reject(new Error(`无法加载图片：${url}`));
          return;
        }

        const fallback = deriveBase64Fallback(url);
        if (!fallback) {
          reject(new Error(`无法加载图片：${url}`));
          return;
        }

        try {
          const response = await fetch(fallback, { cache: 'no-store' });
          if (!response.ok) {
            throw new Error(`无法加载 Base64 资源：${fallback}`);
          }
          const base64 = (await response.text()).trim();
          attempt(`data:image/png;base64,${base64}`, false);
        } catch (error) {
          reject(error);
        }
      };
      img.src = url;
    };

    attempt(src, !src.startsWith('data:'));
  });
}

function deriveBase64Fallback(url) {
  if (!url || url.startsWith('data:')) {
    return null;
  }
  const [path] = url.split('?', 1);
  if (!path.endsWith('.png')) {
    return null;
  }
  return `${path.slice(0, -4)}.b64`;
}

function drawPreviewImage(ctx, image, slot, mode = 'contain') {
  const rect = getSlotRect(slot);
  if (!rect) return;
  const { x, y, width, height } = rect;
  let drawWidth = width;
  let drawHeight = height;

  if (mode === 'cover') {
    const scale = Math.max(width / image.width, height / image.height);
    drawWidth = image.width * scale;
    drawHeight = image.height * scale;
  } else {
    const scale = Math.min(width / image.width, height / image.height);
    drawWidth = image.width * scale;
    drawHeight = image.height * scale;
  }

  const offsetX = x + (width - drawWidth) / 2;
  const offsetY = y + (height - drawHeight) / 2;
  ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight);
}

function drawPreviewPlaceholder(ctx, slot, label) {
  const rect = getSlotRect(slot);
  if (!rect) return;
  const { x, y, width, height } = rect;
  ctx.save();
  ctx.strokeStyle = '#cbd2d9';
  ctx.lineWidth = 2;
  ctx.setLineDash([10, 8]);
  ctx.strokeRect(x + 6, y + 6, Math.max(width - 12, 0), Math.max(height - 12, 0));
  ctx.setLineDash([]);
  drawPreviewText(ctx, label, rect, {
    font: '20px "Noto Sans SC", "Microsoft YaHei", sans-serif',
    color: '#6b7280',
    align: 'center',
    lineHeight: 28,
  });
  ctx.restore();
}

function drawPreviewText(ctx, text, slot, options = {}) {
  if (!text) return;
  const rect = getSlotRect(slot);
  if (!rect) return;
  const { x, y, width, height } = rect;
  ctx.save();
  if (options.font) ctx.font = options.font;
  ctx.fillStyle = options.color || '#1f2933';
  ctx.textBaseline = 'top';
  const lines = wrapPreviewText(ctx, text, width);
  const fontSizeMatch = /([0-9]+(?:\.[0-9]+)?)px/.exec(ctx.font);
  const fontSize = fontSizeMatch ? parseFloat(fontSizeMatch[1]) : 24;
  const lineHeight = options.lineHeight || fontSize * 1.3;
  let offsetY = y;
  lines.forEach((line) => {
    if (offsetY + lineHeight > y + height) return;
    let offsetX = x;
    const measured = ctx.measureText(line);
    if (options.align === 'center') {
      offsetX = x + Math.max((width - measured.width) / 2, 0);
    } else if (options.align === 'right') {
      offsetX = x + Math.max(width - measured.width, 0);
    }
    ctx.fillText(line, offsetX, offsetY);
    offsetY += lineHeight;
  });
  ctx.restore();
}

function wrapPreviewText(ctx, text, maxWidth) {
  const tokens = tokeniseText(text);
  const lines = [];
  let current = '';
  tokens.forEach((token) => {
    if (token === '\n') {
      if (current.trim()) lines.push(current.trim());
      current = '';
      return;
    }
    const candidate = current ? current + token : token;
    const width = ctx.measureText(candidate.trimStart()).width;
    if (width <= maxWidth || !current.trim()) {
      current = candidate;
    } else {
      if (current.trim()) lines.push(current.trim());
      current = token.trimStart();
    }
  });
  if (current.trim()) lines.push(current.trim());
  return lines;
}

function tokeniseText(text) {
  const tokens = [];
  let buffer = '';
  for (const char of text) {
    if (char === '\n') {
      if (buffer) {
        tokens.push(buffer);
        buffer = '';
      }
      tokens.push('\n');
    } else if (char === ' ') {
      buffer += char;
    } else if (/^[A-Za-z0-9]$/.test(char)) {
      buffer += char;
    } else {
      if (buffer) {
        tokens.push(buffer);
        buffer = '';
      }
      tokens.push(char);
    }
  }
  if (buffer) tokens.push(buffer);
  return tokens;
}

  function getSlotRect(slot) {
    if (!slot) return null;
    const x = Number(slot.x) || 0;
    const y = Number(slot.y) || 0;
    const width = Number(slot.width) || 0;
    const height = Number(slot.height) || 0;
    return { x, y, width, height };
  }

function resolveSlotAssetUrl(asset) {
  const direct = pickImageSrc(asset);
  if (direct) return direct;
  if (asset && typeof asset === 'object') {
    const publicUrl = typeof asset.public_url === 'string' ? asset.public_url.trim() : '';
    if (publicUrl) return publicUrl;
    const r2Url = typeof asset.r2_url === 'string' ? asset.r2_url.trim() : '';
    if (r2Url) return r2Url;
  }
  return '';
}

function summariseGenerationSlots(result) {
  const poster = result?.poster || {};
  const scenario =
    pickImageSrc(poster.scenario_image) ||
    pickImageSrc(result?.scenario_image) ||
    null;
  const product =
    pickImageSrc(poster.product_image) ||
    pickImageSrc(result?.product_image) ||
    null;

  const gallerySource = Array.isArray(poster.gallery_images)
    ? poster.gallery_images
    : Array.isArray(result?.gallery_images)
    ? result.gallery_images
    : [];
  const gallery = gallerySource.map((item) => pickImageSrc(item)).filter(Boolean);

  return {
    scenario: Boolean(scenario),
    product: Boolean(product),
    galleryCount: gallery.length,
    gallery,
    posterUrl: extractVertexPosterUrl(result),
  };
}

function surfaceSlotWarnings(slotSummary) {
  if (!slotSummary) return;
  const aiMessage = document.getElementById('ai-preview-message');
  if (!aiMessage) return;

  const missing = [];
  if (!slotSummary.scenario) missing.push('场景图');
  if (!slotSummary.product) missing.push('产品图');
  const missingGallery = slotSummary.galleryCount === 0;

  if (!missing.length && !missingGallery) return;

  const parts = [];
  if (missing.length) parts.push(`缺少${missing.join('、')}`);
  if (missingGallery) parts.push('未返回系列小图');

  aiMessage.textContent = `生成完成，但${parts.join('，')}，请检查素材或稍后重试。`;
}

function renderDualPosterPreview(root, layout, data) {
  if (!root || !layout || !layout.slots) return;
  root.innerHTML = '';
  root.classList.add('poster-layout');
  root.style.position = 'relative';
  if (layout.canvas?.width && layout.canvas?.height) {
    root.style.aspectRatio = `${layout.canvas.width} / ${layout.canvas.height}`;
  }

  const slots = layout.slots;
  Object.entries(slots).forEach(([key, slot]) => {
    if (!slot) return;
    const slotEl = document.createElement('div');
    slotEl.classList.add('poster-layout__slot', `poster-layout__slot--${key}`);
    slotEl.style.left = `${(slot.x ?? 0) * 100}%`;
    slotEl.style.top = `${(slot.y ?? 0) * 100}%`;
    slotEl.style.width = `${(slot.w ?? 0) * 100}%`;
    slotEl.style.height = `${(slot.h ?? 0) * 100}%`;

    if (slot.type === 'text') {
      slotEl.classList.add('poster-layout__slot--text');
      const textValue = data?.text?.[key] || '';
      slotEl.textContent = textValue;
      const fontSize = Math.max((slot.h || 0) * 80, 12);
      slotEl.style.fontSize = `${fontSize}px`;
      if (slot.align === 'right') {
        slotEl.style.justifyContent = 'flex-end';
        slotEl.style.textAlign = 'right';
      } else if (slot.align === 'left') {
        slotEl.style.justifyContent = 'flex-start';
        slotEl.style.textAlign = 'left';
      } else {
        slotEl.style.justifyContent = 'center';
        slotEl.style.textAlign = 'center';
      }
    } else {
      slotEl.classList.add('poster-layout__slot--image');
      const img = document.createElement('img');
      const src = resolveSlotAssetUrl(data?.images?.[key]);
      if (src) {
        img.src = src;
      } else {
        slotEl.style.background = '#f5f5f7';
      }
      slotEl.appendChild(img);
    }

    root.appendChild(slotEl);
  });
}

function buildDualPosterData(stage1Data, generation) {
  const poster = generation?.poster || {};
  const galleryEntries = Array.isArray(stage1Data?.gallery_entries)
    ? stage1Data.gallery_entries.filter(Boolean)
    : [];
  const galleryLabels = galleryEntries.map((item) => item?.caption || '');
  const stage1GallerySources = galleryEntries
    .map((entry) => resolveSlotAssetUrl(entry?.asset))
    .filter(Boolean);

  const generationGallery = Array.isArray(poster.gallery_images)
    ? poster.gallery_images
    : Array.isArray(generation?.gallery_images)
    ? generation.gallery_images
    : [];

  const logoSrc =
    resolveSlotAssetUrl(poster.brand_logo) || resolveSlotAssetUrl(stage1Data?.brand_logo);
  const scenarioSrc =
    resolveSlotAssetUrl(poster.scenario_image) ||
    resolveSlotAssetUrl(generation?.scenario_image) ||
    resolveSlotAssetUrl(stage1Data?.scenario_asset);
  const productSrc =
    resolveSlotAssetUrl(poster.product_image) ||
    resolveSlotAssetUrl(generation?.product_image) ||
    resolveSlotAssetUrl(stage1Data?.product_asset);

  const galleryImages = [];
  for (let i = 0; i < 4; i += 1) {
    const genSrc = resolveSlotAssetUrl(generationGallery[i]);
    const stage1Src = stage1GallerySources.length
      ? stage1GallerySources[i % stage1GallerySources.length]
      : '';
    galleryImages.push(genSrc || stage1Src || logoSrc || '');
  }

  const images = {
    logo: logoSrc || '',
    scenario: scenarioSrc || '',
    product: productSrc || '',
    series_1_img: galleryImages[0] || '',
    series_2_img: galleryImages[1] || '',
    series_3_img: galleryImages[2] || '',
    series_4_img: galleryImages[3] || '',
  };

  const text = {
    brand_name: stage1Data?.brand_name || poster.brand_name || '',
    agent_name: stage1Data?.agent_name || poster.agent_name || '',
    headline: stage1Data?.title || poster.title || '',
    tagline: stage1Data?.subtitle || poster.subtitle || '',
    series_1_txt: galleryLabels[0] || '',
    series_2_txt: galleryLabels[1] || '',
    series_3_txt: galleryLabels[2] || '',
    series_4_txt: galleryLabels[3] || '',
  };

  return { images, text };
}

function refreshPosterLayoutPreview(generationOverride = null) {
  if (!posterLayoutRoot || !lastStage1Data) return;
  const data = buildDualPosterData(lastStage1Data, generationOverride ?? lastPosterResult);
  renderDualPosterPreview(posterLayoutRoot, TEMPLATE_DUAL_LAYOUT, data);
}

let html2CanvasLoader = null;
async function loadHtml2Canvas() {
  if (typeof window !== 'undefined' && window.html2canvas) return window.html2canvas;
  if (html2CanvasLoader) return html2CanvasLoader;

  html2CanvasLoader = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
    script.async = true;
    script.onload = () => resolve(window.html2canvas);
    script.onerror = () => reject(new Error('html2canvas 加载失败'));
    document.head.appendChild(script);
  });

  return html2CanvasLoader;
}

async function saveStage2Result(data) {
  if (!data) return;

  let previousKey = null;
  const previousVariantKeys = new Set();
  const existingRaw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (existingRaw) {
    try {
      const existing = JSON.parse(existingRaw);
      previousKey = existing?.poster_image?.storage_key || null;
      if (Array.isArray(existing?.variants)) {
        existing.variants.forEach((variant) => {
          if (variant?.storage_key) {
            previousVariantKeys.add(variant.storage_key);
          }
        });
      }
    } catch (error) {
      console.warn('无法解析现有的环节 2 数据，跳过旧键清理。', error);
    }
  }

  const payload = { ...data };
  if (data.poster_image) {
    const key = data.poster_image.storage_key || createId();
    const source = getPosterImageSource(data.poster_image);
    if (source) {
      await assetStore.put(key, source);
    }
    payload.poster_image = {
      filename: data.poster_image.filename,
      media_type: data.poster_image.media_type,
      width: data.poster_image.width,
      height: data.poster_image.height,
      storage_key: key,
    };
    if (previousKey && previousKey !== key) {
      await assetStore.delete(previousKey).catch(() => undefined);
    }
  }

  if (Array.isArray(data.variants)) {
    payload.variants = [];
    const usedVariantKeys = new Set();
    for (const variant of data.variants) {
      if (!variant) continue;
      const key = variant.storage_key || createId();
      const source = getPosterImageSource(variant);
      if (source) {
        await assetStore.put(key, source);
      }
      payload.variants.push({
        filename: variant.filename,
        media_type: variant.media_type,
        width: variant.width,
        height: variant.height,
        storage_key: key,
      });
      usedVariantKeys.add(key);
    }
    previousVariantKeys.forEach((key) => {
      if (!usedVariantKeys.has(key)) {
        void assetStore.delete(key).catch(() => undefined);
      }
    });
  }

  try {
    sessionStorage.setItem(STORAGE_KEYS.stage2, JSON.stringify(payload));
  } catch (error) {
    if (isQuotaError(error)) {
      console.warn('sessionStorage 容量不足，正在覆盖旧的环节 2 结果。', error);
      try {
        sessionStorage.removeItem(STORAGE_KEYS.stage2);
        sessionStorage.setItem(STORAGE_KEYS.stage2, JSON.stringify(payload));
      } catch (innerError) {
        console.error('无法保存环节 2 结果，已放弃持久化。', innerError);
      }
    } else {
      console.error('保存环节 2 结果失败。', error);
    }
  }
}

async function loadStage2Result() {
  const raw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.poster_image?.storage_key) {
      const storedValue = await assetStore.get(parsed.poster_image.storage_key);
      if (storedValue) {
        applyStoredAssetValue(parsed.poster_image, storedValue);
      }
    }
    if (Array.isArray(parsed?.variants)) {
      await Promise.all(
        parsed.variants.map(async (variant) => {
          if (variant?.storage_key) {
            const storedValue = await assetStore.get(variant.storage_key);
            if (storedValue) {
              applyStoredAssetValue(variant, storedValue);
            }
          }
        })
      );
    }
    return parsed;
  } catch (error) {
    console.error('Unable to parse stage2 result', error);
    return null;
  }
}

function initStage3() {
  void (async () => {
    const statusElement = document.getElementById('stage3-status');
    const posterImage = document.getElementById('stage3-poster-image');
    const posterCaption = document.getElementById('stage3-poster-caption');
    const promptTextarea = document.getElementById('stage3-prompt');
    const emailRecipient = document.getElementById('email-recipient');
    const emailSubject = document.getElementById('email-subject');
    const emailBody = document.getElementById('email-body');
    const sendButton = document.getElementById('send-email');

    if (!sendButton || !emailRecipient || !emailSubject || !emailBody) {
      return;
    }

    const stage1Data = loadStage1Data();
    const stage2Result = await loadStage2Result();

    if (!stage1Data || !stage2Result?.poster_image) {
      setStatus(statusElement, '请先完成环节 1 与环节 2，生成海报后再发送邮件。', 'warning');
      sendButton.disabled = true;
      return;
    }

    // Prefer active variant (B) when present for preview and sending
    let chosenPosterImage = stage2Result.poster_image;
    try {
      const raw = sessionStorage.getItem('marketing-poster-stage2-variants') || '{}';
      const st = JSON.parse(raw || '{}');
      if (
        st.active === 'B' &&
        Array.isArray(stage2Result.variants) &&
        stage2Result.variants[1]
      ) {
        const candidate = stage2Result.variants[1];
        if (
          candidate.storage_key ||
          candidate.url ||
          candidate.data_url ||
          candidate.remoteUrl
        ) {
          chosenPosterImage = candidate;
        }
      }
    } catch (e) {}

    assignPosterImage(posterImage, chosenPosterImage, `${stage1Data.product_name} 海报预览`);
    if (posterCaption) {
      posterCaption.textContent = `${stage1Data.brand_name} · ${stage1Data.agent_name}`;
    }
    if (promptTextarea) {
      promptTextarea.value = stage2Result.prompt || '';
    }

    emailSubject.value = buildEmailSubject(stage1Data);
    emailRecipient.value = stage1Data.default_recipient || DEFAULT_EMAIL_RECIPIENT;
    emailBody.value = stage2Result.email_body || '';

    sendButton.addEventListener('click', async () => {
      const apiCandidates = getApiCandidates(apiBaseInput?.value || null);
      if (!apiCandidates.length) {
        setStatus(statusElement, '未找到可用的后端基址，无法发送邮件。', 'warning');
        return;
      }

      const recipient = emailRecipient.value.trim();
      const subject = emailSubject.value.trim();
      const body = emailBody.value.trim();

      if (!recipient || !subject || !body) {
        setStatus(statusElement, '请完整填写收件邮箱、主题与正文。', 'error');
        return;
      }

      sendButton.disabled = true;
      setStatus(statusElement, '正在发送营销邮件…', 'info');

      try {
        await warmUp(apiCandidates);

        // Prefer the active variant (B) when sending the attachment
        let attachmentToSend = stage2Result.poster_image;
        try {
          const raw = sessionStorage.getItem('marketing-poster-stage2-variants') || '{}';
          const st = JSON.parse(raw || '{}');
          if (
            st.active === 'B' &&
            Array.isArray(stage2Result.variants) &&
            stage2Result.variants[1]
          ) {
            const candidate = stage2Result.variants[1];
            if (
              candidate.storage_key ||
              candidate.url ||
              candidate.data_url ||
              candidate.remoteUrl
            ) {
              attachmentToSend = candidate;
            }
          }
        } catch (e) {}

        const response = await postJsonWithRetry(
          apiCandidates,
          '/api/send-email',
          {
            recipient,
            subject,
            body,
            attachment: attachmentToSend,
          },
          1
        );

        console.log('邮件发送 response:', response);
        if (response?.status === 'sent') {
          setStatus(statusElement, '营销邮件发送成功！', 'success');
        } else if (response?.status === 'skipped') {
          setStatus(
            statusElement,
            response?.detail || '邮件服务未配置，本次只做预览，未真正发送。',
            'warning'
          );
        } else if (response?.status === 'error') {
          setStatus(
            statusElement,
            response?.detail ? `邮件发送失败：${response.detail}` : '邮件发送失败',
            'error'
          );
        } else {
          setStatus(statusElement, '邮件发送结果未知，请检查日志。', 'warning');
        }
      } catch (error) {
        console.error('[邮件发送失败]', error);
        setStatus(statusElement, error.message || '发送邮件失败，请稍后重试。', 'error');
      } finally {
        sendButton.disabled = false;
      }
    });
  })();
}

// ✉️ 构造邮件标题
function buildEmailSubject(stage1Data) {
  const brand = stage1Data.brand_name || '品牌';
  const agent = stage1Data.agent_name ? `（${stage1Data.agent_name}）` : '';
  const product = stage1Data.product_name || '产品';
  return `${brand}${agent} ${product} 市场推广海报`;
}
function setStatus(element, message, level = 'info') {
  if (!element) return;
  element.textContent = message;
  element.className = level ? `status-${level}` : '';
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result?.toString() || '');
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
}

function createPlaceholder(text) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="300">\n    <defs>\n      <style>\n        .bg { fill: #e5e9f0; }\n        .border { fill: none; stroke: #cbd2d9; stroke-width: 4; stroke-dasharray: 12 10; }\n        .label {\n          font-size: 26px;\n          font-family: 'Segoe UI', 'Noto Sans', sans-serif;\n          font-weight: 600;\n          fill: #3d4852;\n        }\n      </style>\n    </defs>\n    <rect class="bg" x="0" y="0" width="420" height="300" rx="28" />\n    <rect class="border" x="16" y="16" width="388" height="268" rx="24" />\n    <text class="label" x="50%" y="50%" dominant-baseline="middle" text-anchor="middle">${text}</text>\n  </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function getGalleryPlaceholder(index, label = MATERIAL_DEFAULT_LABELS.gallery) {
  const baseLabel = label || MATERIAL_DEFAULT_LABELS.gallery;
  const key = `${baseLabel}-${index}`;
  if (!galleryPlaceholderCache.has(key)) {
    galleryPlaceholderCache.set(
      key,
      createPlaceholder(`${baseLabel} ${index + 1}`)
    );
  }
  return galleryPlaceholderCache.get(key);
}

async function buildAsset(file, dataUrl, previousAsset, options = {}) {
  const { remoteUrl = null, r2Key = null } = options;
  const isDataUrl = typeof dataUrl === 'string' && dataUrl.startsWith('data:');
  let storageKey = previousAsset?.key || null;

  if (isDataUrl && dataUrl) {
    const newKey = createId();
    await assetStore.put(newKey, dataUrl);
    if (previousAsset?.key && previousAsset.key !== newKey) {
      await assetStore.delete(previousAsset.key).catch(() => undefined);
    }
    storageKey = newKey;
  } else if (previousAsset?.key) {
    await assetStore.delete(previousAsset.key).catch(() => undefined);
    storageKey = null;
  }

  const previewSource = dataUrl || remoteUrl || null;

  return {
    key: storageKey,
    dataUrl: previewSource,
    remoteUrl: remoteUrl || (previewSource && !isDataUrl ? previewSource : null),
    r2Key: r2Key || null,
    name: file?.name || previousAsset?.name || null,
    type: file?.type || previousAsset?.type || null,
    size:
      typeof file?.size === 'number'
        ? file.size
        : typeof previousAsset?.size === 'number'
        ? previousAsset.size
        : null,
    lastModified:
      typeof file?.lastModified === 'number'
        ? file.lastModified
        : typeof previousAsset?.lastModified === 'number'
        ? previousAsset.lastModified
        : Date.now(),
  };
}

async function prepareAssetFromFile(
  folder,
  file,
  previousAsset,
  statusElement,
  options = {}
) {
  const {
    forceDataUrl = false,
    requireUpload = false,
    requireUploadMessage,
  } = options;
  const candidates = getApiCandidates(apiBaseInput?.value || null);
  let uploadResult = null;

  if (candidates.length) {
    uploadResult = await uploadFileToR2(folder, file, { bases: candidates });
    if (!uploadResult.uploaded) {
      if (requireUpload) {
        throw new Error(
          requireUploadMessage || '素材上传失败，请确认对象存储配置。'
        );
      }
      if (statusElement) {
        const message =
          uploadResult.error instanceof Error
            ? uploadResult.error.message
            : '上传到 R2 失败，已回退至本地预览。';
        setStatus(statusElement, message, 'warning');
      }
    }
  } else if (requireUpload) {
    throw new Error(
      requireUploadMessage || '请先配置后端基址以启用对象存储上传。'
    );
  } else if (statusElement) {
    setStatus(statusElement, '未配置后端基址，素材将仅保存在本地预览。', 'warning');
  }

  const remoteUrl = uploadResult?.url || null;
  if (requireUpload && !remoteUrl) {
    throw new Error(
      requireUploadMessage || '素材上传失败，请确认对象存储配置。'
    );
  }
  let dataUrl = uploadResult?.dataUrl || null;
  if (!dataUrl || (!forceDataUrl && remoteUrl)) {
    dataUrl = !remoteUrl || forceDataUrl ? await fileToDataUrl(file) : remoteUrl;
  }

  return buildAsset(file, dataUrl, previousAsset, {
    remoteUrl,
    r2Key: uploadResult?.key || null,
  });
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function serialiseAssetForStorage(asset) {
  if (!asset) return null;
  const { key, name, type, size, lastModified, dataUrl, remoteUrl, r2Key } = asset;
  const isDataUrl = typeof dataUrl === 'string' && dataUrl.startsWith('data:');
  return {
    key: key || null,
    name: name || null,
    type: type || null,
    size: typeof size === 'number' ? size : null,
    lastModified: typeof lastModified === 'number' ? lastModified : null,
    remoteUrl: !isDataUrl ? dataUrl || remoteUrl || null : remoteUrl || null,
    r2Key: r2Key || null,
  };
}

async function rehydrateStoredAsset(assetMeta) {
  if (!assetMeta) return null;
  if (assetMeta.dataUrl && typeof assetMeta.dataUrl === 'string') {
    return assetMeta;
  }
  if (assetMeta.remoteUrl) {
    return { ...assetMeta, dataUrl: assetMeta.remoteUrl };
  }
  if (!assetMeta.key) {
    return { ...assetMeta, dataUrl: null };
  }
  const dataUrl = await assetStore.get(assetMeta.key);
  if (!dataUrl) {
    return { ...assetMeta, dataUrl: null };
  }
  return { ...assetMeta, dataUrl };
}

async function hydrateStage1DataAssets(stage1Data) {
  if (!stage1Data) return stage1Data;
  stage1Data.brand_logo = await rehydrateStoredAsset(stage1Data.brand_logo);
  stage1Data.scenario_asset = await rehydrateStoredAsset(stage1Data.scenario_asset);
  stage1Data.product_asset = await rehydrateStoredAsset(stage1Data.product_asset);
  if (Array.isArray(stage1Data.gallery_entries)) {
    stage1Data.gallery_entries = await Promise.all(
      stage1Data.gallery_entries.map(async (entry) => ({
        ...entry,
        asset: await rehydrateStoredAsset(entry.asset),
        mode:
          entry.mode === 'logo' || entry.mode === 'logo_fallback'
            ? 'upload'
            : entry.mode,
      }))
    );
  }
  return stage1Data;
}

async function deleteStoredAsset(asset) {
  if (asset?.key) {
    await assetStore.delete(asset.key).catch(() => undefined);
  }
}

function isQuotaError(error) {
  if (typeof DOMException === 'undefined') return false;
  return (
    error instanceof DOMException &&
    (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED')
  );
}

function createAssetStore() {
  const DB_NAME = 'marketing-poster-assets';
  const STORE_NAME = 'assets';
  const VERSION = 1;
  const memoryStore = new Map();
  const supportsIndexedDB = typeof indexedDB !== 'undefined';
  let dbPromise = null;

  function openDb() {
    if (!supportsIndexedDB) return Promise.resolve(null);
    if (!dbPromise) {
      dbPromise = new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, VERSION);
        request.onupgradeneeded = () => {
          const db = request.result;
          if (!db.objectStoreNames.contains(STORE_NAME)) {
            db.createObjectStore(STORE_NAME);
          }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error || new Error('无法打开 IndexedDB'));
      }).catch((error) => {
        console.warn('IndexedDB 不可用，回退到内存存储。', error);
        return null;
      });
    }
    return dbPromise;
  }

  async function put(key, value) {
    if (!key) return null;
    const db = await openDb();
    if (!db) {
      memoryStore.set(key, value);
      return key;
    }
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.onabort = () => {
        console.warn('IndexedDB 写入失败，使用内存存储。', tx.error);
        memoryStore.set(key, value);
        resolve(key);
      };
      tx.oncomplete = () => resolve(key);
      const store = tx.objectStore(STORE_NAME);
      const request = store.put(value, key);
      request.onerror = () => {
        tx.abort();
      };
    });
  }

  async function get(key) {
    if (!key) return null;
    const db = await openDb();
    if (!db) {
      return memoryStore.get(key) || null;
    }
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      tx.onabort = () => {
        console.warn('IndexedDB 读取失败，使用内存存储。', tx.error);
        resolve(memoryStore.get(key) || null);
      };
      const store = tx.objectStore(STORE_NAME);
      const request = store.get(key);
      request.onsuccess = () => {
        const result = request.result;
        if (result) {
          resolve(result);
        } else {
          resolve(memoryStore.get(key) || null);
        }
      };
      request.onerror = () => {
        tx.abort();
      };
    });
  }

  async function remove(key) {
    if (!key) return;
    const db = await openDb();
    if (!db) {
      memoryStore.delete(key);
      return;
    }
    await new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.oncomplete = () => resolve();
      tx.onabort = () => {
        console.warn('IndexedDB 删除失败，尝试清理内存存储。', tx.error);
        memoryStore.delete(key);
        resolve();
      };
      tx.objectStore(STORE_NAME).delete(key);
    });
    memoryStore.delete(key);
  }

  async function clear() {
    const db = await openDb();
    if (db) {
      await new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.oncomplete = () => resolve();
        tx.onabort = () => resolve();
        tx.objectStore(STORE_NAME).clear();
      });
    }
    memoryStore.clear();
  }

  return {
    put,
    get,
    delete: remove,
    clear,
  };
}

if (typeof window.openABModal !== 'function') {
  window.openABModal = function openABModal(layout) {
    console.log('[openABModal] stub called, layout =', layout);
    alert('A/B 测试弹窗暂未实现，目前已完成 AI 海报生成，可以先前往第 3 步使用该海报。');
  };
}
