const App = (window.App ??= {});
App.utils = App.utils ?? {};

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

const HEALTH_CACHE_TTL = 60_000;
const HEALTH_CACHE = new Map();

let documentAssetBase = null;

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

function joinBasePath(base, path) {
  const normalised = normaliseBase(base);
  if (!normalised) return null;
  const suffix = path.startsWith('/') ? path : `/${path}`;
  return `${normalised}${suffix}`;
}

function ensureArray(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}

const warmUpLocks = new Map();

function getApiCandidates(extra) {
  const candidates = new Set();
  const addCandidate = (value) => {
    const trimmed = typeof value === 'string' ? value.trim() : '';
    if (!trimmed) return;
    const normalised = normaliseBase(trimmed);
    if (normalised) {
      candidates.add(normalised);
    }
  };

  const inputValue = document.getElementById('api-base')?.value;
  addCandidate(inputValue);

  const stored = localStorage.getItem(STORAGE_KEYS?.apiBase ?? '');
  addCandidate(stored);

  const bodyDataset = document.body?.dataset ?? {};
  addCandidate(bodyDataset.workerBase);
  addCandidate(bodyDataset.renderBase);
  addCandidate(bodyDataset.apiBase);

  if (Array.isArray(window.APP_API_BASES)) {
    window.APP_API_BASES.forEach(addCandidate);
  }
  addCandidate(window.APP_WORKER_BASE);
  addCandidate(window.APP_RENDER_BASE);
  addCandidate(window.APP_DEFAULT_API_BASE);

  if (extra) {
    ensureArray(extra).forEach(addCandidate);
  }

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


async function warmUp(baseOrBases, { force } = {}) {
  const bases = ensureArray(baseOrBases).filter(Boolean);
  const targets = bases.length ? bases : getApiCandidates();
  if (!targets.length) return [];

  const lockKey = targets.sort().join('|');
  if (!force && warmUpLocks.has(lockKey)) {
    return warmUpLocks.get(lockKey);
  }

  const task = Promise.allSettled(targets.map((base) => probeBase(base, { force })));
  warmUpLocks.set(lockKey, task.finally(() => warmUpLocks.delete(lockKey)));
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

function validatePayloadSize(rawPayload) {
  if (!rawPayload) return;
  const encoder = new TextEncoder();
  const size = encoder.encode(rawPayload).length;
  const hasBase64 = /data:[^;]+;base64,/i.test(rawPayload);
  if (hasBase64 || size > 300_000) {
    throw new Error('请求体过大或包含 base64 图片，请先上传素材到 R2，仅传输 key/url。');
  }
}

async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload) {
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

async function r2PresignPut(folder, file, bases) {
  const payload = {
    folder: folder || 'uploads',
    filename: file?.name || 'upload.bin',
    content_type: file?.type || 'application/octet-stream',
    size: typeof file?.size === 'number' ? file.size : null,
  };
  const response = await postJsonWithRetry(bases, '/api/r2/presign-put', payload, 1);
  return response.json();
}

async function uploadFileToR2(folder, file, options = {}) {
  try {
    const presign = await r2PresignPut(folder, file, options?.bases);
    const putResponse = await fetch(presign.put_url, {
      method: 'PUT',
      headers: { 'Content-Type': file?.type || 'application/octet-stream' },
      body: file,
    });
    if (!putResponse.ok) {
      const detail = await putResponse.text();
      throw new Error(detail || '上传到 R2 失败，请稍后重试。');
    }
    return {
      key: presign.key,
      url: presign.public_url || null,
      uploaded: true,
      presign,
    };
  } catch (error) {
    console.warn('[uploadFileToR2] 直传失败，回退本地预览', error);
    const dataUrl = file ? await fileToDataUrl(file) : null;
    return {
      key: null,
      url: null,
      uploaded: false,
      dataUrl,
      error,
    };
  }
}

App.utils.r2PresignPut = r2PresignPut;
App.utils.uploadFileToR2 = uploadFileToR2;

function applyStoredAssetValue(target, storedValue) {
  if (!target || typeof storedValue !== 'string') return;
  if (storedValue.startsWith('data:')) {
    target.data_url = storedValue;
  } else {
    target.url = storedValue;
  }
}

const apiBaseInput = document.getElementById('api-base');

init();

function init() {
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
      const assets = await ensureTemplateAssets(templateId);
      await applyTemplateMaterialsStage1(assets.spec);
      const ctx = templateCanvasStage1.getContext('2d');
      if (!ctx) return;
      const { width, height } = templateCanvasStage1;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#f8fafc';
      ctx.fillRect(0, 0, width, height);
      const image = assets.image;
      const scale = Math.min(width / image.width, height / image.height);
      const drawWidth = image.width * scale;
      const drawHeight = image.height * scale;
      const offsetX = (width - drawWidth) / 2;
      const offsetY = (height - drawHeight) / 2;
      ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight);
      if (templateDescriptionStage1) {
        templateDescriptionStage1.textContent = assets.entry?.description || '';
      }
    } catch (error) {
      console.error(error);
      if (templateDescriptionStage1) {
        templateDescriptionStage1.textContent = '模板预览加载失败，请检查模板资源。';
      }
      if (templateCanvasStage1) {
        const ctx = templateCanvasStage1.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, templateCanvasStage1.width, templateCanvasStage1.height);
          ctx.fillStyle = '#f4f5f7';
          ctx.fillRect(0, 0, templateCanvasStage1.width, templateCanvasStage1.height);
          ctx.fillStyle = '#6b7280';
          ctx.font = '16px "Noto Sans SC", "Microsoft YaHei", sans-serif';
          ctx.fillText('模板预览加载失败', 24, 48);
        }
      }
    }
  }

  if (templateSelectStage1) {
    loadTemplateRegistry()
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

  renderGalleryItems(state, galleryItemsContainer, {
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement,
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
  state.scenario = await rehydrateStoredAsset(data.scenario_asset);
  state.product = await rehydrateStoredAsset(data.product_asset);
  state.galleryEntries = Array.isArray(data.gallery_entries)
    ? await Promise.all(
        data.gallery_entries.map(async (entry) => ({
          id: entry.id || createId(),
          caption: entry.caption || '',
          asset: await rehydrateStoredAsset(entry.asset),
          mode: entry.mode || 'upload',
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
      const forceDataUrl = key === 'brandLogo';
      state[key] = await prepareAssetFromFile(
        folder,
        file,
        state[key],
        statusElement,
        { forceDataUrl }
      );
      if (inlinePreview) {
        inlinePreview.src = state[key]?.dataUrl ||
          (key === 'brandLogo'
            ? placeholderImages.brandLogo
            : key === 'scenario'
            ? placeholderImages.scenario
            : placeholderImages.product);
      }
      state.previewBuilt = false;
      refreshPreview();
    } catch (error) {
      console.error(error);
      setStatus(statusElement, '处理图片素材时发生错误，请重试。', 'error');
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
    item.classList.add('gallery-item');
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
        previewImage.src = entry.asset?.dataUrl || placeholder;
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
    const previewImage = document.createElement('img');
    previewImage.alt = `${label} ${index + 1} 预览`;
    previewImage.src = entry.asset?.dataUrl || placeholder;
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
    promptTextarea.addEventListener('input', () => {
      entry.prompt = promptTextarea.value;
      state.previewBuilt = false;
      onChange?.();
    });
    promptField.appendChild(promptTextarea);
    item.appendChild(promptField);

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
        previewImage.src = entry.asset?.dataUrl || placeholder;
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

  if (brandLogo) {
    brandLogo.src = payload.brand_logo?.dataUrl || placeholderImages.brandLogo;
  }
  if (brandName) {
    brandName.textContent = payload.brand_name || '品牌名称';
  }
  if (agentName) {
    agentName.textContent = (payload.agent_name || '代理名 / 分销名').toUpperCase();
  }
  if (scenarioImage) {
    scenarioImage.src = payload.scenario_asset?.dataUrl || placeholderImages.scenario;
  }
  if (productImage) {
    productImage.src = payload.product_asset?.dataUrl || placeholderImages.product;
  }
  if (title) {
    title.textContent = payload.title || '标题文案';
  }
  if (subtitle) {
    subtitle.textContent = payload.subtitle || '副标题文案';
  }

  if (featureList) {
    featureList.innerHTML = '';
    const featuresForPreview = payload.features.length
      ? payload.features
      : DEFAULT_STAGE1.features;
    featuresForPreview.slice(0, 4).forEach((feature, index) => {
      const item = document.createElement('li');
      item.classList.add(`feature-tag-${index + 1}`);
      item.textContent = feature || `功能点 ${index + 1}`;
      featureList.appendChild(item);
    });
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
      const img = document.createElement('img');
      const caption = document.createElement('figcaption');
      if (entry?.asset?.dataUrl) {
        img.src = entry.asset.dataUrl;
      } else {
        img.src = getGalleryPlaceholder(index, galleryLabel);
      }
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
    const posterImage = document.getElementById('poster-image');
    const variantsStrip = document.getElementById('poster-variants');
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

    let promptManager = null;
    let currentTemplateAssets = null;
    let latestPromptState = null;
    let promptPresets = null;

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
          promptBundlePre.textContent = bundleText;
          promptBundleGroup.classList.remove('hidden');
        } else {
          promptBundlePre.textContent = '';
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

      return triggerGeneration({
        stage1Data,
        statusElement,
        layoutStructure,
        posterOutput,
        aiPreview,
        aiSpinner,
        aiPreviewMessage,
        posterVisual,
        posterImage,
        variantsStrip,
        promptGroup,
        emailGroup,
        promptTextarea,
        emailTextarea,
        generateButton,
        regenerateButton,
        nextButton,
        promptManager,
        updatePromptPanels,
        ...extra,
      }).catch((error) => console.error(error));
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
      const request = promptManager?.buildRequest?.() || { variants: 2 };
      runGeneration({
        forceVariants: Math.max(2, request.variants || 2),
        abTest: true,
      });
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
        const assets = await ensureTemplateAssets(templateId);
        currentTemplateAssets = assets;
        if (templateDescription) {
          templateDescription.textContent = assets.entry?.description || '';
        }
        const previewAssets = await prepareTemplatePreviewAssets(stage1Data);
        drawTemplatePreview(templateCanvas, assets, stage1Data, previewAssets);
        updatePromptPanels({ spec: assets.spec });
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
      }
    }

    if (templateSelect && templateCanvas) {
      try {
        templateRegistry = await loadTemplateRegistry();
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

async function triggerGeneration(options) {
  const {
    stage1Data,
    statusElement,
    layoutStructure,
    posterOutput,
    aiPreview,
    aiSpinner,
    aiPreviewMessage,
    posterVisual,
    posterImage,
    variantsStrip,
    promptGroup,
    emailGroup,
    promptTextarea,
    emailTextarea,
    generateButton,
    regenerateButton,
    nextButton,
    promptManager,
    updatePromptPanels,
    forceVariants = null,
    abTest = false,
  } = options;

  const apiCandidates = getApiCandidates(apiBaseInput?.value || null);
  if (!apiCandidates.length) {
    setStatus(statusElement, '未找到可用的后端基址，请填写或配置 Render / Worker 地址。', 'warning');
    return null;
  }

  await hydrateStage1DataAssets(stage1Data);

  const templateId = stage1Data.template_id || DEFAULT_STAGE1.template_id;

  const scenarioAsset = stage1Data.scenario_asset || null;
  const productAsset = stage1Data.product_asset || null;

  const payload = {
    brand_name: stage1Data.brand_name,
    agent_name: stage1Data.agent_name,
    scenario_image: stage1Data.scenario_image,
    product_name: stage1Data.product_name,
    template_id: templateId,
    features: stage1Data.features,
    title: stage1Data.title,
    subtitle: stage1Data.subtitle,
    series_description: stage1Data.series_description,
    brand_logo: stage1Data.brand_logo?.dataUrl || null,
    scenario_asset:
      scenarioAsset && scenarioAsset.r2Key
        ? null
        : scenarioAsset?.dataUrl && scenarioAsset.dataUrl.startsWith('data:')
        ? scenarioAsset.dataUrl
        : null,
    scenario_key: scenarioAsset?.r2Key || null,
    product_asset:
      productAsset && productAsset.r2Key
        ? null
        : productAsset?.dataUrl && productAsset.dataUrl.startsWith('data:')
        ? productAsset.dataUrl
        : null,
    product_key: productAsset?.r2Key || null,
    scenario_mode: stage1Data.scenario_mode || 'upload',
    scenario_prompt:
      stage1Data.scenario_mode === 'prompt'
        ? stage1Data.scenario_prompt || stage1Data.scenario_image
        : null,
    product_mode: stage1Data.product_mode || 'upload',
    product_prompt: stage1Data.product_prompt || null,
    gallery_items:
      stage1Data.gallery_entries?.map((entry) => {
        const asset = entry.asset || null;
        const dataUrl = asset?.dataUrl;
        const r2Key = asset?.r2Key || null;
        const serialisedAsset =
          r2Key || !(typeof dataUrl === 'string' && dataUrl.startsWith('data:'))
            ? null
            : dataUrl;
        return {
          caption: entry.caption?.trim() || null,
          asset: serialisedAsset,
          key: r2Key,
          mode: entry.mode || 'upload',
          prompt: entry.prompt?.trim() || null,
        };
      }) || [],
  };

  const promptConfig = promptManager?.buildRequest?.() || {
    prompts: {},
    variants: DEFAULT_PROMPT_VARIANTS,
    seed: null,
    lockSeed: false,
  };
  if (forceVariants) {
    promptConfig.variants = clampVariants(forceVariants);
  }
  const promptSnapshot = JSON.parse(JSON.stringify(promptConfig));
  const requestPayload = {
    poster: payload,
    render_mode: 'locked',
    variants: promptConfig.variants,
    seed: promptConfig.seed,
    lock_seed: Boolean(promptConfig.lockSeed),
    prompts: promptConfig.prompts,
  };

  if (typeof updatePromptPanels === 'function') {
    updatePromptPanels({ bundle: promptSnapshot.prompts });
  }

  const rawPayload = JSON.stringify(requestPayload);
  try {
    validatePayloadSize(rawPayload);
  } catch (validationError) {
    setStatus(statusElement, validationError.message, 'error');
    return null;
  }

  generateButton.disabled = true;
  if (regenerateButton) {
    regenerateButton.disabled = true;
  }
  const statusMessage = abTest
    ? '正在进行 A/B 提示词生成…'
    : '正在生成海报与营销文案…';
  setStatus(statusElement, statusMessage, 'info');

  if (posterOutput) posterOutput.classList.remove('hidden');
  if (aiPreview) aiPreview.classList.remove('complete');
  if (aiSpinner) aiSpinner.classList.remove('hidden');
  if (aiPreviewMessage) aiPreviewMessage.textContent = 'Glibatree Art Designer 正在绘制海报…';
  if (posterVisual) posterVisual.classList.add('hidden');
  if (promptGroup) promptGroup.classList.add('hidden');
  if (emailGroup) emailGroup.classList.add('hidden');
  if (nextButton) nextButton.disabled = true;
  if (variantsStrip) {
    variantsStrip.innerHTML = '';
    variantsStrip.classList.add('hidden');
  }

  try {
    await warmUp(apiCandidates);
    // 将对象型的 prompt（如 {preset, aspect, text}）转换成后端需要的纯字符串
function toPromptString(x) {
  if (x == null) return '';
  if (typeof x === 'string') return x.trim();

  // 你如果已经在别处算出了最终文案，可能放在 .text / .prompt 字段
  if (typeof x.text === 'string')   return x.text.trim();
  if (typeof x.prompt === 'string') return x.prompt.trim();

  // 只有 preset/aspect 的情况：至少给后端一个可读字符串，避免 500
  if (x.preset && x.aspect) return `${x.preset} (aspect ${x.aspect})`;
  if (x.preset)             return String(x.preset);

  // 兜底：把对象压成一行字符串，保证类型正确（不建议长期使用）
  try { return JSON.stringify(x); } catch { return String(x); }
}

// 统一把 prompt_bundle 三个字段收敛为字符串
if (payload && payload.prompt_bundle) {
  const b = payload.prompt_bundle;
  payload.prompt_bundle = {
    scenario: toPromptString(b.scenario),
    product : toPromptString(b.product),
    gallery : toPromptString(b.gallery),
  };
}

    const response = await postJsonWithRetry(apiCandidates, '/api/generate-poster', requestPayload, 2, rawPayload);

    const data = await response.json();
    if (layoutStructure && data.layout_preview) {
      layoutStructure.textContent = data.layout_preview;
    }
    if (
      assignPosterImage(
        posterImage,
        data.poster_image,
        `${payload.product_name} 海报预览`
      )
    ) {
      // Assigned successfully
    }
    const promptDetails = data.prompt_details || null;
    if (promptTextarea) {
      if (data.prompt) {
        promptTextarea.value = data.prompt;
      } else if (data.prompt_bundle) {
        const bundleText =
          typeof data.prompt_bundle === 'string'
            ? data.prompt_bundle
            : JSON.stringify(data.prompt_bundle, null, 2);
        promptTextarea.value = bundleText;
      } else if (promptManager?.getState) {
        promptTextarea.value = buildPromptPreviewText(promptManager.getState());
      } else {
        promptTextarea.value = '';
      }
    }
    console.info('[Stage2] OpenAI prompt payload:', data.prompt || data.prompt_bundle || '(no prompt returned)');
    if (typeof updatePromptPanels === 'function') {
      updatePromptPanels({ bundle: data.prompt_bundle || promptSnapshot.prompts });
    }
    if (emailTextarea) {
      emailTextarea.value = data.email_body || '';
    }
    if (variantsStrip) {
      variantsStrip.innerHTML = '';
      const variants = Array.isArray(data.variants) ? data.variants : [];
      if (variants.length > 1) {
        variantsStrip.classList.remove('hidden');
        variants.forEach((variant, index) => {
          const variantSrc = getPosterImageSource(variant);
          if (!variantSrc) return;
          const card = document.createElement('div');
          card.className = 'variant-card';
          const img = document.createElement('img');
          img.src = variantSrc;
          img.alt = `${payload.product_name} 海报变体 ${index + 1}`;
          card.appendChild(img);
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'secondary';
          button.textContent = '设为主图';
          button.addEventListener('click', async () => {
            assignPosterImage(
              posterImage,
              variant,
              `${payload.product_name} 海报变体 ${index + 1}`
            );
            await saveStage2Result({
              poster_image: variant,
              prompt: data.prompt || data.prompt_bundle || '',
              prompt_details: promptDetails,
              email_body: data.email_body,
              template_id: payload.template_id,
              variants: data.variants || [],
              prompt_config: promptSnapshot,
              scores: data.scores || null,
            });
            setStatus(statusElement, `已切换至变体 ${index + 1}`, 'info');
          });
          card.appendChild(button);
          variantsStrip.appendChild(card);
        });
      } else {
        variantsStrip.classList.add('hidden');
      }
    }
    if (aiPreview) aiPreview.classList.add('complete');
    if (aiSpinner) aiSpinner.classList.add('hidden');
    if (aiPreviewMessage) aiPreviewMessage.textContent = 'AI 生成完成，以下为最新输出。';
    if (posterVisual) posterVisual.classList.remove('hidden');
    if (promptGroup) promptGroup.classList.remove('hidden');
    if (emailGroup) emailGroup.classList.remove('hidden');
    if (nextButton) nextButton.disabled = false;

    setStatus(statusElement, '海报与营销文案生成完成。', 'success');

    const stage2Result = {
      poster_image: data.poster_image,
      prompt: data.prompt || data.prompt_bundle || '',
      prompt_details: promptDetails,
      email_body: data.email_body,
      template_id: payload.template_id,
      variants: data.variants || [],
      prompt_config: promptSnapshot,
      scores: data.scores || null,
    };
    if (promptManager?.applyBackend && data.prompt_bundle) {
      promptManager.applyBackend(data.prompt_bundle);
    }
    await saveStage2Result(stage2Result);
    return stage2Result;
  } catch (error) {
    console.error(error);
    setStatus(statusElement, error.message || '生成海报时发生错误。', 'error');
    if (aiPreview) aiPreview.classList.add('complete');
    if (aiSpinner) aiSpinner.classList.add('hidden');
    if (aiPreviewMessage) aiPreviewMessage.textContent = '生成失败，请稍后重试。';
    if (posterVisual) posterVisual.classList.add('hidden');
    if (promptGroup) promptGroup.classList.add('hidden');
    if (emailGroup) emailGroup.classList.add('hidden');
    if (nextButton) nextButton.disabled = true;
    if (typeof updatePromptPanels === 'function') {
      updatePromptPanels();
    }
    return null;
  } finally {
    generateButton.disabled = false;
    if (regenerateButton) {
      regenerateButton.disabled = false;
      regenerateButton.classList.remove('hidden');
    }
  }
}

async function loadTemplateRegistry() {
  if (!templateRegistryPromise) {
    templateRegistryPromise = fetch(assetUrl(TEMPLATE_REGISTRY_PATH))
      .then((response) => {
        if (!response.ok) {
          throw new Error('无法加载模板清单');
        }
        return response.json();
      })
      .catch((error) => {
        templateRegistryPromise = null;
        throw error;
      });
  }
  const registry = await templateRegistryPromise;
  return Array.isArray(registry) ? registry : [];
}

async function ensureTemplateAssets(templateId) {
  if (templateCache.has(templateId)) {
    return templateCache.get(templateId);
  }
  const registry = await loadTemplateRegistry();
  const entry =
    registry.find((item) => item.id === templateId) || registry.find((item) => item.id);
  if (!entry) {
    throw new Error('模板列表为空');
  }
  const [spec, image] = await Promise.all([
    fetch(assetUrl(`templates/${entry.spec}`)).then((response) => {
      if (!response.ok) throw new Error('无法加载模板规范');
      return response.json();
    }),
    loadImageAsset(assetUrl(`templates/${entry.preview}`)),
  ]);

  const payload = { entry, spec, image };
  templateCache.set(entry.id, payload);
  return payload;
}

async function prepareTemplatePreviewAssets(stage1Data) {
  const result = {
    brand_logo: null,
    scenario: null,
    product: null,
    gallery: [],
  };

  const tasks = [];
  const queue = (key, dataUrl, index) => {
    if (!dataUrl) return;
    tasks.push(
      loadImageAsset(dataUrl)
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

  queue('brand_logo', stage1Data.brand_logo?.dataUrl);
  queue('scenario', stage1Data.scenario_asset?.dataUrl);
  queue('product', stage1Data.product_asset?.dataUrl);
  (stage1Data.gallery_entries || []).forEach((entry, index) => {
    queue('gallery', entry?.asset?.dataUrl, index);
  });

  await Promise.allSettled(tasks);
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

    assignPosterImage(
      posterImage,
      stage2Result.poster_image,
      `${stage1Data.product_name} 海报预览`
    );
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
        const response = await postJsonWithRetry(
          apiCandidates,
          '/api/send-email',
          {
            recipient,
            subject,
            body,
            attachment: stage2Result.poster_image,
          },
          1
        );

        await response.json().catch(() => ({}));
        setStatus(statusElement, '营销邮件发送成功！', 'success');
      } catch (error) {
        console.error(error);
        setStatus(statusElement, error.message || '发送邮件失败，请稍后重试。', 'error');
      } finally {
        sendButton.disabled = false;
      }
    });
  })();
}

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
  const { forceDataUrl = false } = options;
  const candidates = getApiCandidates(apiBaseInput?.value || null);
  let uploadResult = null;

  if (candidates.length) {
    uploadResult = await uploadFileToR2(folder, file, { bases: candidates });
    if (!uploadResult.uploaded && statusElement) {
      const message =
        uploadResult.error instanceof Error
          ? uploadResult.error.message
          : '上传到 R2 失败，已回退至本地预览。';
      setStatus(statusElement, message, 'warning');
    }
  } else if (statusElement) {
    setStatus(statusElement, '未配置后端基址，素材将仅保存在本地预览。', 'warning');
  }

  const remoteUrl = uploadResult?.url || null;
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
