
const App = (window.App ??= {});
App.utils = App.utils ?? {};

// Always resolve assets relative to the current document base.
App.utils.assetUrl = (relPath) => new URL(relPath, document.baseURI).toString();

const MODE_S = true;
const MODE_S_RENDER_MODE = 'kitposter1_a';

const VERTEX_IMAGE_TAG_CLASSNAMES = {
  scenario: 'slot-scenario',
  product: 'slot-product',
  gallery: 'slot-gallery',
};
let apiBaseInput;
const STAGE2_PROD_API_BASE = 'https://ai-service-leob.onrender.com';
const DEPRECATED_STAGE2_API_BASES = new Set([
  'https://ai-service-x758.onrender.com',
]);

function isDeprecatedApiBase(value) {
  const normalised = normaliseBase(value);
  return Boolean(normalised && DEPRECATED_STAGE2_API_BASES.has(normalised));
}

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
  const fallbackWarning = document.getElementById('asset-fallback-warning');
  const candidates = [];
  if (typeof url === 'string' && url.trim()) candidates.push(url.trim());

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

  if (slot === 'scenario') {
    candidates.push(DEFAULT_SCENARIO_ASSET, LOCAL_PLACEHOLDER_IMAGE, placeholderImages.scenario);
  } else if (slot === 'product') {
    candidates.push(LOCAL_PLACEHOLDER_IMAGE, placeholderImages.product);
  } else {
    if (typeof logoFallback === 'string' && logoFallback.trim()) {
      candidates.push(logoFallback.trim());
    }
    if (logoImg?.src) {
      candidates.push(logoImg.src);
    }
  }

  if (!candidates.length) return;

  selectors
    .map((selector) => document.querySelectorAll(selector))
    .forEach((nodeList) => {
      nodeList.forEach((img) => {
        if (img && img.tagName === 'IMG') {
          applyImageWithFallback(img, candidates, fallbackWarning);
        }
      });
    });
}

let lastStage1Data = null;
let lastPosterResult = null;
let posterLayoutRoot = null;

// --- Stage2: 缓存最近一次生成结果，给 A/B 对比、重放使用 ---
const posterGenerationState = {
  /** 本次生成用到的 prompt 结构，用于展示 / 调试 */
  promptBundle: null,
  /** Vertex / Glibatree 返回的原始响应，必要时可做更多调试 */
  rawResult: null,
};
// 兼容旧版调用：确保引用不存在的全局变量时不会抛出 ReferenceError
let posterGeneratedImage = null;
let posterGeneratedLayout = null;

// stage2：缓存最近一次生成结果与提示词，便于预览与回放
let lastPromptBundle = null;
const stage2RequestHelpers = globalThis.Stage2RequestHelpers || {};
let stage2ActiveRequestId = 0;
let stage2ActiveAbortController = null;
let stage2LastSourceSignatures = null;
let stage2RemovedBottomModeRemapLogged = false;
let stage2IgnoredThumbnailsOverrideLogged = false;
let stage2LastSuccessfulFormSignature = null;
let stage2LastSuccessfulRequestSignature = null;

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
  vertex: {
    lastResponse: null,
  },
  poster2: {
    rendererMode: 'auto',
    history: [],
    latestResult: null,
    copyOptimization: {
      mode: 'suggest',
      decision: 'pending',
      acceptedTitle: '',
      acceptedSubtitle: '',
      acceptedFeatures: [],
      latestReview: null,
    },
    bottomContract: {
      title: '',
      subtitle: '',
      bottomMode: 'title_gallery_split',
      galleryMode: 'strip_local_visible_only',
    },
  },
  generated: {
    attempted: false,
    lastSuccessPosterUrl: null,
  },
  generationAction: 'generate',
  regenPolicy: {
    updateScenario: false,
    updateGallery: false,
    updateProduct: false,
  },
    adjustments: {
      showBullets: true,
      titleScale: 1,
      qualityMode: 'stable',
      titleSize: 'M',
      fallbackStableClicked: false,
    },
  renderMode: 'kitposter1_a',
};
let stage2HasAttemptedGenerate = false;
let stage2LastGeneratedAssetFingerprint = null;
let stage2GenerationSeq = 0;
let stage2InFlight = false;
let stage2GenerateInFlight = false;
let stage2LastClickAt = 0;
const STAGE2_CLICK_DEBOUNCE_MS = 700;
let stage2RunGeneration = null;
const STAGE2_REVEAL_DELAY_MS = 500;
const STAGE2_RENDER_MODE_KEY = 'marketing-poster-render-mode';
const STAGE2_POSTER2_RENDERER_MODE_KEY = 'marketing-poster-v2-renderer-mode';
const POSTER2_PILOT_SOURCE_TEMPLATE_ID = 'template_dual';
const POSTER2_PILOT_TEMPLATE_ID = 'template_dual_v2';
const POSTER2_BOTTOM_TITLE_MAX_CHARS = 120;
const POSTER2_BOTTOM_SUBTITLE_MAX_CHARS = 120;
const STAGE1_PRODUCT_CALLOUT_MAX_ITEMS = 3;
const FRONTEND_BASELINE_STAMP = 'ee1cd4c';
const BACKEND_BASELINE_EXPECTED = 'ee1cd4c';

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function initStage2RenderModeControl(promptInspector, statusElement) {
  if (!promptInspector) return null;
  const header = promptInspector.querySelector('header');
  if (!header) return null;

  const seedControls = header.querySelector('.seed-controls');
  const wrapper = document.createElement('div');
  wrapper.className = 'seed-controls';
  wrapper.style.marginTop = '8px';

  const label = document.createElement('label');
  const labelText = document.createElement('span');
  labelText.textContent = 'Render Mode';
  const select = document.createElement('select');
  select.id = 'stage2-render-mode';
  select.innerHTML = `
    <option value="kitposter1_a">KitPoster A (default)</option>
    <option value="kitposter1_b">KitPoster B</option>
    <option value="locked">Legacy locked</option>
  `;

  label.appendChild(labelText);
  label.appendChild(select);
  wrapper.appendChild(label);

  const hint = document.createElement('p');
  hint.className = 'hint';
  hint.textContent = 'KitPoster 1.0 uses locked inpaint; Legacy locked falls back to old pipeline.';
  wrapper.appendChild(hint);

  if (seedControls && seedControls.parentNode) {
    seedControls.parentNode.insertBefore(wrapper, seedControls.nextSibling);
  } else {
    header.appendChild(wrapper);
  }

  const stored = sessionStorage.getItem(STAGE2_RENDER_MODE_KEY);
  const defaultMode = stored || stage2State.renderMode || 'kitposter1_a';
  stage2State.renderMode = defaultMode;
  select.value = defaultMode;

  select.addEventListener('change', () => {
    stage2State.renderMode = select.value;
    sessionStorage.setItem(STAGE2_RENDER_MODE_KEY, select.value);
    if (statusElement) {
      setStatus(statusElement, `Render mode 已切换为 ${select.value}。`, 'info');
    }
  });

  return select;
}

function ensureStage2FinalPosterPreview(container) {
  if (!container) return null;
  if (document.getElementById('final-poster-img')) return null;
  let wrapper = document.getElementById('stage2-final-poster');
  if (wrapper) return wrapper;

  wrapper = document.createElement('div');
  wrapper.id = 'stage2-final-poster';
  wrapper.className = 'output-group hidden';

  const title = document.createElement('h3');
  title.textContent = 'Final Poster (KitPoster)';

  const link = document.createElement('a');
  link.id = 'stage2-final-poster-link';
  link.className = 'poster-preview-link hidden';
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.textContent = 'Open full image';

  const img = document.createElement('img');
  img.id = 'stage2-final-poster-image';
  img.alt = 'Final poster preview';
  img.style.maxWidth = '100%';
  img.style.display = 'block';

  wrapper.appendChild(title);
  wrapper.appendChild(link);
  wrapper.appendChild(img);

  container.appendChild(wrapper);
  return wrapper;
}

function shouldUsePoster2Pilot(stage1Data) {
  return (stage1Data?.template_id || '') === POSTER2_PILOT_SOURCE_TEMPLATE_ID;
}

function initStage2Poster2PilotControls(stage1Data, statusElement) {
  const panel = document.getElementById('poster2-pilot-panel');
  const select = document.getElementById('poster2-renderer-mode');
  const hint = document.getElementById('poster2-pilot-hint');
  const badge = document.getElementById('poster2-pilot-badge');
  const copy = document.getElementById('poster2-pilot-copy');
  if (!panel || !select || !hint || !badge || !copy) return;

  const eligible = shouldUsePoster2Pilot(stage1Data);
  const stored = sessionStorage.getItem(STAGE2_POSTER2_RENDERER_MODE_KEY);
  stage2State.poster2.rendererMode = stored || stage2State.poster2.rendererMode || 'auto';
  select.value = stage2State.poster2.rendererMode;

  if (eligible) {
    panel.classList.remove('hidden');
    select.disabled = false;
    badge.textContent = 'Internal-only pilot';
    hint.textContent = 'template_dual uses /api/v2/generate-poster with template_dual_v2. Pillow remains the safe default; Puppeteer is opt-in only.';
    copy.textContent = 'template_dual_v2 is in internal-only Puppeteer pilot. Use this selector to validate pillow vs puppeteer from the product UI.';
  } else {
    panel.classList.remove('hidden');
    select.value = 'auto';
    select.disabled = true;
    stage2State.poster2.rendererMode = 'auto';
    badge.textContent = 'Safe default only';
    hint.textContent = 'This template stays on the existing safe/default renderer path. Puppeteer pilot is limited to template_dual_v2.';
    copy.textContent = 'template_dual_v2 is the only internal-only Puppeteer pilot template. Other templates stay on safe/default renderer.';
  }

  select.addEventListener('change', () => {
    stage2State.poster2.rendererMode = select.value;
    sessionStorage.setItem(STAGE2_POSTER2_RENDERER_MODE_KEY, select.value);
    if (statusElement && eligible) {
      setStatus(statusElement, `Poster2 renderer 已切换为 ${select.value}。`, 'info');
    }
  });
}

function normalisePoster2BottomText(value, maxChars) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!text) return '';
  return text.slice(0, maxChars);
}

function isModeSTemplateAFamilyPath(source) {
  const variant = typeof source?.template_variant === 'string' ? source.template_variant.trim().toLowerCase() : 'a';
  return MODE_S && variant !== 'b';
}

function isModeSGenericAgentText(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!text) return true;
  const lower = text.toLowerCase();
  if (AGENT_NAME_PLACEHOLDERS.has(lower)) return true;
  return (
    text.includes('渠道服务中心') ||
    lower.includes('service center') ||
    lower.includes('channel service')
  );
}

function resolveModeSAgentName(candidate, brandName = '') {
  const text = typeof candidate === 'string' ? candidate.trim() : '';
  if (MODE_S && isModeSGenericAgentText(text)) {
    return MODE_S_DEFAULT_STAGE1.agent_name;
  }
  return sanitizeAgentName(text, brandName);
}

function resolveTemplateABottomSupportCopy(source, fallback = '') {
  const subtitle = typeof source?.subtitle === 'string' ? source.subtitle.trim() : '';
  if (subtitle) return subtitle;
  const legacyTagline = typeof source?.tagline === 'string' ? source.tagline.trim() : '';
  if (legacyTagline) return legacyTagline;
  if (isModeSTemplateAFamilyPath(source)) {
    return MODE_S_DEFAULT_STAGE1.subtitle || fallback;
  }
  return fallback;
}

function hasPoster2BottomField(bottom, key) {
  return Boolean(bottom) && Object.prototype.hasOwnProperty.call(bottom, key);
}

function resolvePoster2BottomFallbackText(stage1Data, field) {
  const candidates = field === 'title'
    ? [
        [isModeSTemplateAFamilyPath(stage1Data) ? MODE_S_DEFAULT_BOTTOM_TITLE : '', 'mode_s.default_bottom_title'],
        [stage1Data?.title, 'stage1.title'],
        [isModeSTemplateAFamilyPath(stage1Data) ? MODE_S_DEFAULT_STAGE1.title : '', 'mode_s.default_title'],
        ['Poster', 'literal.default_title'],
      ]
    : [
        [stage1Data?.subtitle, 'stage1.subtitle'],
        [stage1Data?.tagline, 'stage1.tagline'],
        [isModeSTemplateAFamilyPath(stage1Data) ? MODE_S_DEFAULT_STAGE1.subtitle : '', 'mode_s.default_subtitle'],
        [stage1Data?.promo, 'stage1.promo'],
        [stage1Data?.price, 'stage1.price'],
        ['', 'literal.empty'],
      ];

  for (const [value, source] of candidates) {
    const text = typeof value === 'string' ? value.trim() : '';
    if (!text && source !== 'literal.empty') continue;
    return { text, source };
  }

  return {
    text: field === 'title' ? 'Poster' : '',
    source: field === 'title' ? 'literal.default_title' : 'literal.empty',
  };
}

function canonicalizePoster2BottomMode(rawMode) {
  const mode = typeof rawMode === 'string' ? rawMode.trim() : '';
  const aliases = {
    title_only: 'text_only_expanded',
    title_only_expand: 'text_only_expanded',
    text_gallery_expanded: 'title_gallery_split',
  };
  const canonical = aliases[mode] || mode || 'title_gallery_split';
  const allowedModes = new Set([
    'title_gallery_split',
    'text_only_expanded',
    'gallery_only',
  ]);
  if (mode === 'text_gallery_expanded' && !stage2RemovedBottomModeRemapLogged) {
    stage2RemovedBottomModeRemapLogged = true;
    console.info('[stage2] bottom_mode remapped', {
      from: 'text_gallery_expanded',
      to: 'title_gallery_split',
      reason: 'removed_from_operator_surface',
    });
  }
  return allowedModes.has(canonical) ? canonical : 'title_gallery_split';
}

function countStage1GalleryAssets(stage1Data) {
  if (typeof stage2RequestHelpers.countStage1GalleryAssets === 'function') {
    return stage2RequestHelpers.countStage1GalleryAssets(stage1Data);
  }
  const entries = Array.isArray(stage1Data?.gallery_entries) ? stage1Data.gallery_entries : [];
  return entries
    .filter((entry) => {
      const asset = entry?.asset;
      if (!asset) return false;
      if (typeof asset === 'string') return Boolean(asset.trim());
      if (typeof asset !== 'object') return false;
      return Boolean(
        asset.key ||
          asset.r2Key ||
          asset.storage_key ||
          asset.url ||
          asset.remoteUrl ||
          asset.publicUrl ||
          asset.public_url ||
          asset.asset_url ||
          asset.src ||
          asset.dataUrl ||
          asset.data_url
      );
    })
    .slice(0, 4)
    .length;
}

function logIgnoredStaleThumbnailsOverride() {
  if (stage2IgnoredThumbnailsOverrideLogged) return;
  stage2IgnoredThumbnailsOverrideLogged = true;
  console.info('[stage2] ignored stale operator override', {
    field: 'thumbnails',
    action: 'ignored_stale_stage2_override',
    source: 'stale_local_or_hydrated_state',
  });
}

function updateDetectedGalleryCountDisplay(stage1Data) {
  const display = document.getElementById('poster2-detected-gallery-count');
  if (!display) return;
  const count = countStage1GalleryAssets(stage1Data);
  display.textContent = `Detected gallery items: ${count}`;
  display.dataset.galleryCount = String(count);
}

function ensurePoster2BottomContractState(stage1Data) {
  const bottom = stage2State.poster2?.bottomContract || {};
  const defaultTitle = resolvePoster2BottomFallbackText(stage1Data, 'title');
  const defaultSubtitle = resolvePoster2BottomFallbackText(stage1Data, 'subtitle');
  if (
    Object.prototype.hasOwnProperty.call(bottom, 'galleryCount') ||
    Object.prototype.hasOwnProperty.call(bottom, 'autoFillGallery')
  ) {
    logIgnoredStaleThumbnailsOverride();
  }
  const modeSTemplateA = isModeSTemplateAFamilyPath(stage1Data);
  const resolvedTitle = hasPoster2BottomField(bottom, 'title')
    ? normalisePoster2BottomText(bottom.title, POSTER2_BOTTOM_TITLE_MAX_CHARS)
    : normalisePoster2BottomText(defaultTitle.text, POSTER2_BOTTOM_TITLE_MAX_CHARS);
  const resolvedSubtitle = hasPoster2BottomField(bottom, 'subtitle')
    ? normalisePoster2BottomText(bottom.subtitle, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS)
    : normalisePoster2BottomText(defaultSubtitle.text, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS);

  stage2State.poster2.bottomContract = {
    title: modeSTemplateA ? (resolvedTitle || normalisePoster2BottomText(defaultTitle.text, POSTER2_BOTTOM_TITLE_MAX_CHARS)) : resolvedTitle,
    subtitle: modeSTemplateA ? (resolvedSubtitle || normalisePoster2BottomText(defaultSubtitle.text, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS)) : resolvedSubtitle,
    titleSource: hasPoster2BottomField(bottom, 'titleSource')
      ? bottom.titleSource
      : defaultTitle.source,
    subtitleSource: hasPoster2BottomField(bottom, 'subtitleSource')
      ? bottom.subtitleSource
      : defaultSubtitle.source,
    bottomMode: canonicalizePoster2BottomMode(bottom.bottomMode),
    galleryMode: bottom.galleryMode || 'strip_local_visible_only',
  };

  return stage2State.poster2.bottomContract;
}

function buildPoster2BottomRequestState(stage1Data) {
  const bottom = ensurePoster2BottomContractState(stage1Data);
  const canonicalBottomMode = canonicalizePoster2BottomMode(bottom.bottomMode);
  bottom.bottomMode = canonicalBottomMode;
  const requestedTitleText = normalisePoster2BottomText(bottom.title, POSTER2_BOTTOM_TITLE_MAX_CHARS);
  const requestedSubtitleText = normalisePoster2BottomText(bottom.subtitle, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS);
  const detectedGalleryCount = countStage1GalleryAssets(stage1Data);

  return {
    requested_title_text: requestedTitleText,
    requested_subtitle_text: requestedSubtitleText,
    sanitized_title_text: requestedTitleText,
    sanitized_subtitle_text: requestedSubtitleText,
    title_source: bottom.titleSource || 'stage2.bottom_contract.title',
    subtitle_source: bottom.subtitleSource || 'stage2.bottom_contract.subtitle',
    bottom_mode: canonicalBottomMode,
    gallery_mode: bottom.galleryMode || 'strip_local_visible_only',
    gallery_input_count_raw: detectedGalleryCount,
    gallery_input_count_normalized: detectedGalleryCount,
    requested_gallery_count: detectedGalleryCount,
    gallery_autofill_applied: false,
    auto_fill_gallery: false,
  };
}

function syncPoster2BottomContractFromControls(stage1Data) {
  const bottom = ensurePoster2BottomContractState(stage1Data);
  const titleInput = document.getElementById('poster2-bottom-title');
  const subtitleInput = document.getElementById('poster2-bottom-subtitle');
  const bottomMode = document.getElementById('poster2-bottom-mode');
  const galleryMode = document.getElementById('poster2-gallery-mode');

  if (titleInput) {
    bottom.title = normalisePoster2BottomText(titleInput.value, POSTER2_BOTTOM_TITLE_MAX_CHARS);
    bottom.titleSource = 'stage2.bottom_contract.title';
  }
  if (subtitleInput) {
    bottom.subtitle = normalisePoster2BottomText(subtitleInput.value, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS);
    bottom.subtitleSource = 'stage2.bottom_contract.subtitle';
  }
  if (bottomMode) {
    const canonicalBottomMode = canonicalizePoster2BottomMode(bottomMode.value);
    bottom.bottomMode = canonicalBottomMode;
    bottomMode.value = canonicalBottomMode;
  }
  if (galleryMode) {
    bottom.galleryMode = galleryMode.value || 'strip_local_visible_only';
  }
  updateDetectedGalleryCountDisplay(stage1Data);
  return bottom;
}

function updatePoster2BottomRequestPreview(stage1Data) {
  const preview = document.getElementById('poster2-bottom-request-preview');
  if (!preview) return;
  preview.textContent = JSON.stringify(buildPoster2BottomRequestState(stage1Data), null, 2);
}

// ── Template-family visibility: hide Family A controls for Template B ──────
const TEMPLATE_B_ID = 'template_product_sheet_v1';

function isTemplateBTemplateId(templateId) {
  return (templateId || '').trim() === TEMPLATE_B_ID;
}

function isTemplateBStage1Data(stage1Data) {
  if (!stage1Data || typeof stage1Data !== 'object') return false;
  if (isTemplateBTemplateId(stage1Data.template_id)) return true;
  return (stage1Data.template_variant || '') === 'b';
}

function normaliseTemplateBMaterials(stage1Data) {
  const rawMaterials = Array.isArray(stage1Data?.materials_images)
    ? stage1Data.materials_images
    : Array.isArray(stage1Data?.materialsImages)
    ? stage1Data.materialsImages
    : [];
  return rawMaterials.filter((entry) => entry && (entry.url || entry.key || entry.dataUrl));
}

function buildTemplateBStage2State(stage1Data) {
  const materials = normaliseTemplateBMaterials(stage1Data);
  return {
    template_display: 'template_product_sheet_v1 · Family B product sheet',
    region_order: 'logo_banner -> top_copy -> materials_strip -> product_hero -> description',
    title: stage1Data?.title || '',
    subtitle: stage1Data?.subtitle || '',
    sku_text: stage1Data?.sku_text || '',
    description_title: stage1Data?.description_title || stage1Data?.descriptionTitle || '',
    description_body: stage1Data?.description_body || stage1Data?.descriptionBody || '',
    materials_count: materials.length,
    materials_state: materials.length ? `${materials.length} accessory / sample image(s) ready` : '0 accessory / sample images',
    primary_product_state: stage1Data?.product_image_1 ? 'primary ready' : 'primary missing',
    secondary_product_state: stage1Data?.product_image_2 ? 'supporting detail ready' : 'supporting detail optional',
  };
}

function renderTemplateBStage2Summary(stage1Data) {
  const summary = buildTemplateBStage2State(stage1Data);
  const setValue = (id, value, fallback = '—') => {
    const el = document.getElementById(id);
    if (el) el.value = value || fallback;
  };
  setValue('s2-b-title', summary.title);
  setValue('s2-b-subtitle', summary.subtitle);
  setValue('s2-b-sku', summary.sku_text);
  setValue('s2-b-description-title', summary.description_title);
  setValue('s2-b-description-body', summary.description_body);
  setValue('s2-b-materials-state', summary.materials_state);
  setValue(
    's2-b-image-state',
    `${summary.primary_product_state}; ${summary.secondary_product_state}`
  );
}

function applyStage2TemplateFamilyVisibility(stage1Data) {
  const isTemplateB = isTemplateBStage1Data(stage1Data);

  // Bottom Region panel (gallery/mode controls) — Family A only
  const bottomPanel = document.getElementById('s2-bottom-region-panel');
  if (bottomPanel) bottomPanel.style.display = isTemplateB ? 'none' : '';

  const familyACopyFields = document.getElementById('s2-family-a-copy-fields');
  if (familyACopyFields) familyACopyFields.style.display = isTemplateB ? 'none' : '';

  const templateBSummary = document.getElementById('s2-template-b-summary');
  if (templateBSummary) templateBSummary.classList.toggle('hidden', !isTemplateB);

  const copyOptimizationPanel = document.getElementById('poster2-copy-optimization-panel');
  if (copyOptimizationPanel) copyOptimizationPanel.classList.toggle('hidden', isTemplateB);

  // "Bottom Support Copy" textarea — Family A only (maps to bottom subtitle band)
  const bottomCopyField = document.getElementById('s2-bottom-support-copy-field');
  if (bottomCopyField) bottomCopyField.style.display = isTemplateB ? 'none' : '';

  // Product Callouts display is Family A-oriented; Template B uses dedicated summary.
  const featuresSection = document.getElementById('s2-features-section');
  if (featuresSection) featuresSection.style.display = isTemplateB ? 'none' : '';

  // Template display label
  const templateDisplay = document.getElementById('s2-template-display');
  if (templateDisplay) {
    templateDisplay.value = isTemplateB
      ? 'template_product_sheet_v1 · Family B'
      : 'template_dual_v2 · Family A';
  }

  const templateBadge = document.getElementById('s2-template-badge');
  if (templateBadge) {
    templateBadge.textContent = isTemplateB ? 'template_product_sheet_v1' : 'template_dual_v2';
  }

  const rendererModeSelect = document.getElementById('poster2-renderer-mode');
  if (rendererModeSelect && !stage2State.poster2.rendererMode) {
    stage2State.poster2.rendererMode = rendererModeSelect.value || 'auto';
  }

  if (isTemplateB) {
    renderTemplateBStage2Summary(stage1Data);
  }
}

function ensurePoster2CopyOptimizationState() {
  const current = stage2State.poster2?.copyOptimization || {};
  stage2State.poster2.copyOptimization = {
    mode: current.mode || 'suggest',
    decision: current.decision || 'pending',
    acceptedTitle: current.acceptedTitle || '',
    acceptedSubtitle: current.acceptedSubtitle || '',
    acceptedFeatures: Array.isArray(current.acceptedFeatures) ? current.acceptedFeatures.filter(Boolean).slice(0, 4) : [],
    latestReview: current.latestReview || null,
  };
  return stage2State.poster2.copyOptimization;
}

function buildPoster2CopyLineageRow(label, fieldReview) {
  if (!fieldReview) return '';
  const requestedText = fieldReview.requested_text || '—';
  const sanitizedText = fieldReview.sanitized_text || '—';
  const cleanupText = fieldReview.cleanup_text || '—';
  const fitRewriteText = fieldReview.fit_rewrite_text || '—';
  const optimizedText = fieldReview.optimized_text || '—';
  const acceptedText = fieldReview.accepted_text || '—';
  const renderedText = fieldReview.rendered_text || '—';
  const renderedSource = fieldReview.rendered_text_source || 'sanitized_text';
  const changed = optimizedText !== '—' && optimizedText !== sanitizedText;
  return `
    <div class="s2-slot-note"><strong>${label}</strong> ${changed ? '[diff]' : '[same]'}</div>
    <div class="s2-slot-note">requested_text -> ${requestedText}</div>
    <div class="s2-slot-note">sanitized_text -> ${sanitizedText}</div>
    <div class="s2-slot-note">cleanup_text -> ${cleanupText}</div>
    <div class="s2-slot-note">fit_rewrite_text -> ${fitRewriteText}</div>
    <div class="s2-slot-note">optimized_text -> ${optimizedText}</div>
    <div class="s2-slot-note">accepted_text -> ${acceptedText}</div>
    <div class="s2-slot-note">rendered_text -> ${renderedText}</div>
    <div class="s2-slot-note">rendered_text_source -> ${renderedSource}</div>
  `;
}

function buildPoster2AnnotationOptimizationRows(items) {
  if (!Array.isArray(items) || !items.length) return '';
  return items.map((item, index) => buildPoster2CopyLineageRow(`annotation_${index + 1}`, item)).join('');
}

function buildPoster2CopyOptimizationSummary(review, state) {
  const changedFields = Array.isArray(review?.changed_fields) ? review.changed_fields : [];
  const decision = state.decision || review?.decision || 'pending';
  const actionable = Boolean(review?.operator_controls?.can_accept) && changedFields.length > 0;
  const applied = review?.applied_to_rendered_output ? 'true' : 'false';
  const pending = decision === 'pending' ? 'true' : 'false';
  const disabledReason = review?.disabled_reason || review?.operator_controls?.disabled_reason || 'none';
  return `
    <div class="s2-diagnostics-grid">
      <div class="s2-diagnostic-card"><div class="s2-diagnostic-key">mode</div><div class="s2-diagnostic-val">${review?.mode || state.mode}</div></div>
      <div class="s2-diagnostic-card"><div class="s2-diagnostic-key">changed_fields</div><div class="s2-diagnostic-val">${changedFields.length ? changedFields.join(', ') : 'none'}</div></div>
      <div class="s2-diagnostic-card"><div class="s2-diagnostic-key">applied</div><div class="s2-diagnostic-val">${applied}</div></div>
      <div class="s2-diagnostic-card"><div class="s2-diagnostic-key">pending</div><div class="s2-diagnostic-val">${pending}</div></div>
      <div class="s2-diagnostic-card"><div class="s2-diagnostic-key">actionable</div><div class="s2-diagnostic-val">${actionable ? 'true' : 'false'}</div></div>
    </div>
    <div class="s2-slot-note">disabled_reason: ${disabledReason || 'none'}</div>
  `;
}

function buildPoster2CopyOptimizationLineage(review) {
  const titleLine = buildPoster2CopyLineageRow('title', review?.title);
  const subtitleLine = buildPoster2CopyLineageRow('subtitle', review?.subtitle);
  const annotationLine = buildPoster2AnnotationOptimizationRows(review?.annotation_items);
  return `${titleLine}${subtitleLine}${annotationLine}`;
}

function renderPoster2CopyOptimizationReview(review) {
  const state = ensurePoster2CopyOptimizationState();
  state.latestReview = review || null;

  const summary = document.getElementById('poster2-copy-optimization-summary');
  const lineage = document.getElementById('poster2-copy-optimization-lineage');
  const toggleBtn = document.getElementById('poster2-copy-optimization-toggle');
  const acceptBtn = document.getElementById('poster2-copy-optimization-accept');
  const rejectBtn = document.getElementById('poster2-copy-optimization-reject');
  const actions = document.getElementById('poster2-copy-optimization-actions');
  const modeSelect = document.getElementById('poster2-copy-optimization-mode');
  const panel = document.getElementById('poster2-copy-optimization-panel');
  if (modeSelect) modeSelect.value = state.mode || 'off';

  const changedFields = Array.isArray(review?.changed_fields) ? review.changed_fields : [];
  const operatorControls = review?.operator_controls || {};
  const showActions = Boolean(operatorControls.visible) && changedFields.length > 0 && state.mode !== 'off';
  const showLineageToggle = Boolean(review) && (changedFields.length > 0 || state.mode !== 'off');
  const keepCollapsed = !showActions && state.mode === 'off';
  if (summary) {
    if (!review) {
      summary.innerHTML = '<div class="s2-slot-note">暂无 copy optimization review。</div>';
    } else {
      summary.innerHTML = buildPoster2CopyOptimizationSummary(review, state);
    }
  }

  if (lineage) {
    lineage.innerHTML = review ? buildPoster2CopyOptimizationLineage(review) : '';
    lineage.classList.add('hidden');
  }
  if (toggleBtn) {
    toggleBtn.classList.toggle('hidden', !showLineageToggle);
    toggleBtn.textContent = 'Show lineage';
    toggleBtn.onclick = () => {
      if (!lineage) return;
      const nextHidden = !lineage.classList.contains('hidden');
      lineage.classList.toggle('hidden', nextHidden);
      toggleBtn.textContent = nextHidden ? 'Show lineage' : 'Hide lineage';
    };
  }
  if (actions) actions.classList.toggle('hidden', !showActions);
  if (panel) panel.classList.toggle('s2-copy-optimization-compact', keepCollapsed);
  const canAct = Boolean(operatorControls.can_accept) && showActions;
  if (acceptBtn) acceptBtn.disabled = !canAct;
  if (rejectBtn) rejectBtn.disabled = !canAct;
}

function initPoster2CopyOptimizationControls(stage1Data, statusElement) {
  const panel = document.getElementById('poster2-copy-optimization-panel');
  const modeSelect = document.getElementById('poster2-copy-optimization-mode');
  const acceptBtn = document.getElementById('poster2-copy-optimization-accept');
  const rejectBtn = document.getElementById('poster2-copy-optimization-reject');
  if (!panel || !modeSelect || !acceptBtn || !rejectBtn) return;

  const state = ensurePoster2CopyOptimizationState();
  const eligible = shouldUsePoster2Pilot(stage1Data) && !isTemplateBStage1Data(stage1Data);
  panel.classList.toggle('hidden', !eligible);
  modeSelect.value = state.mode || 'suggest';

  modeSelect.onchange = () => {
    state.mode = modeSelect.value || 'off';
    if (state.mode === 'off') {
      state.decision = 'pending';
      state.acceptedTitle = '';
      state.acceptedSubtitle = '';
      state.acceptedFeatures = [];
    }
    invalidateStage2SuccessDerivedState('copy_optimization_mode_changed', ['copy_optimization_acceptance']);
    renderPoster2CopyOptimizationReview(state.latestReview);
  };

  acceptBtn.onclick = () => {
    const review = state.latestReview;
    if (!review) return;
    state.decision = 'accepted';
    state.acceptedTitle = review?.title?.optimized_text || '';
    state.acceptedSubtitle = review?.subtitle?.optimized_text || '';
    state.acceptedFeatures = Array.isArray(review?.annotation_items)
      ? review.annotation_items.map((item) => item?.optimized_text || '').filter(Boolean).slice(0, 4)
      : [];
    renderPoster2CopyOptimizationReview(review);
    if (statusElement) setStatus(statusElement, '已接受 copy optimization，下次生成时生效。', 'info');
  };

  rejectBtn.onclick = () => {
    state.decision = 'rejected';
    state.acceptedTitle = '';
    state.acceptedSubtitle = '';
    state.acceptedFeatures = [];
    renderPoster2CopyOptimizationReview(state.latestReview);
    if (statusElement) setStatus(statusElement, '已拒绝 copy optimization，继续使用 Family A 基础文案。', 'info');
  };

  renderPoster2CopyOptimizationReview(state.latestReview);
}

function initPoster2BottomContractControls(stage1Data, statusElement) {
  const panel = document.getElementById('poster2-bottom-contract-panel');
  const titleInput = document.getElementById('poster2-bottom-title');
  const subtitleInput = document.getElementById('poster2-bottom-subtitle');
  const bottomMode = document.getElementById('poster2-bottom-mode');
  const galleryMode = document.getElementById('poster2-gallery-mode');
  if (!panel || !titleInput || !subtitleInput || !bottomMode || !galleryMode) {
    return;
  }

  const eligible = shouldUsePoster2Pilot(stage1Data);
  panel.classList.toggle('hidden', !eligible);
  // Always wire bottom controls — bottom is SOP baseline regardless of template eligibility

  ensurePoster2BottomContractState(stage1Data);
  const sync = () => {
    const canonicalBottomMode = canonicalizePoster2BottomMode(bottomMode.value);
    const nextTitle = normalisePoster2BottomText(titleInput.value, POSTER2_BOTTOM_TITLE_MAX_CHARS);
    const nextSubtitle = normalisePoster2BottomText(subtitleInput.value, POSTER2_BOTTOM_SUBTITLE_MAX_CHARS);
    titleInput.value = nextTitle;
    subtitleInput.value = nextSubtitle;
    bottomMode.value = canonicalBottomMode;
    stage2State.poster2.bottomContract.title = nextTitle;
    stage2State.poster2.bottomContract.subtitle = nextSubtitle;
    stage2State.poster2.bottomContract.titleSource = 'stage2.bottom_contract.title';
    stage2State.poster2.bottomContract.subtitleSource = 'stage2.bottom_contract.subtitle';
    stage2State.poster2.bottomContract.bottomMode = canonicalBottomMode;
    stage2State.poster2.bottomContract.galleryMode = galleryMode.value;
    updateDetectedGalleryCountDisplay(stage1Data);
    updatePoster2BottomRequestPreview(stage1Data);
    invalidateStage2SuccessDerivedState('bottom_contract_changed', ['bottom_contract']);
  };

  titleInput.value = stage2State.poster2.bottomContract.title;
  subtitleInput.value = stage2State.poster2.bottomContract.subtitle;
  bottomMode.value = canonicalizePoster2BottomMode(stage2State.poster2.bottomContract.bottomMode);
  galleryMode.value = stage2State.poster2.bottomContract.galleryMode;
  updateDetectedGalleryCountDisplay(stage1Data);

  for (const element of [titleInput, subtitleInput, bottomMode, galleryMode]) {
    element.addEventListener('input', sync);
    element.addEventListener('change', sync);
  }
  sync();
  if (statusElement && eligible) {
    setStatus(statusElement, 'Poster2 bottom contract 控件已就绪，可验证。', 'info');
  }
}

function fingerprintAssets(assets) {
  const scenario = assets?.scenario_url || '';
  const product = assets?.product_url || '';
  const gallery = Array.isArray(assets?.gallery_urls) ? assets.gallery_urls.join('|') : '';
  return `${scenario}||${product}||${gallery}`;
}

function updateRegenerateButtonState() {
  const button = document.getElementById('regenerate-poster');
  if (!button) return;
  const attempted = stage2State.generated?.attempted || stage2HasAttemptedGenerate;
  if (!attempted) {
    button.classList.add('hidden');
    button.disabled = true;
    return;
  }
  button.classList.remove('hidden');
  const currentFingerprint = fingerprintAssets(stage2State.assets);
  const isDirty =
    stage2LastGeneratedAssetFingerprint == null
      ? true
      : currentFingerprint !== stage2LastGeneratedAssetFingerprint;
  const shouldDisable = stage2GenerateInFlight || stage2InFlight || !isDirty;
  button.disabled = shouldDisable;
}

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

function setText(elId, text) {
  const el = document.getElementById(elId);
  if (!el) return;
  const value = typeof text === 'string' ? text : String(text ?? '');
  if ('value' in el) {
    el.value = value;
    return;
  }
  el.textContent = value;
}

function renderJson(elId, obj) {
  const el = document.getElementById(elId);
  if (!el) return;
  const payload = obj == null ? '' : JSON.stringify(obj, null, 2);
  if ('value' in el) {
    el.value = payload;
  } else {
    el.textContent = payload;
  }
}

function resolvePreviewAssetSrc(asset) {
  if (!asset) return null;
  if (typeof asset === 'string') return asset.trim() || null;
  const candidates = [
    asset.remoteUrl,
    asset.url,
    asset.publicUrl,
    asset.public_url,
    asset.asset_url,
    asset.src,
    asset.dataUrl,
    asset.data_url,
  ];
  return candidates.find(
    (value) => typeof value === 'string' && (HTTP_URL_RX.test(value) || value.startsWith('data:'))
  ) || null;
}

function buildTemplateAPreviewModel({
  brandName,
  agentName,
  title,
  subtitle,
  features,
  logoSrc,
  scenarioSrc,
  productPrimarySrc,
  productSecondarySrc,
  galleryItems,
  bottomMode = 'title_gallery_split',
  galleryMode = 'strip_local_visible_only',
  latestResult = null,
} = {}) {
  const normalizedGalleryItems = Array.isArray(galleryItems) ? galleryItems.filter(Boolean) : [];
  const truth = resolveTemplateAPreviewTruthLocal({
    titleText: title,
    subtitleText: subtitle,
    agentName,
    featureTexts: Array.isArray(features) ? features : [],
    hasSecondaryAsset: Boolean(productSecondarySrc),
    galleryCount: normalizedGalleryItems.length,
    bottomMode,
    galleryMode,
    latestResult,
  });
  return {
    truth,
    brandName: brandName || '',
    agentName: agentName || '',
    title: title || '',
    subtitle: subtitle || '',
    features: Array.isArray(features) ? features.filter(Boolean).slice(0, 3) : [],
    logoSrc: logoSrc || '',
    scenarioSrc: scenarioSrc || '',
    productPrimarySrc: productPrimarySrc || '',
    productSecondarySrc: truth.showSecondaryInset ? (productSecondarySrc || '') : '',
    galleryItems: truth.galleryVisible ? normalizedGalleryItems : [],
  };
}

function applyTemplateAPreviewModel({
  root,
  brandLogoEl,
  brandNameEl,
  agentNameEl,
  scenarioImageEl,
  productImageEl,
  productSecondaryImageEl,
  productSecondaryWrapEl,
  featureListEl,
  titleEl,
  subtitleEl,
  galleryEl,
  model,
  galleryPlaceholderLabel = MATERIAL_DEFAULT_LABELS.gallery,
} = {}) {
  if (!model) return;
  const truth = model.truth || {};
  if (root) {
    root.dataset.previewProductComposition = truth.productComposition || '';
    root.dataset.previewProductGeometryMode = truth.productGeometryMode || '';
    root.dataset.previewFooterOrdering = truth.footerOrdering || '';
    root.dataset.previewBottomMode = truth.bottomMode || '';
    root.classList.toggle('poster-preview--with-supporting-inset', Boolean(truth.showSecondaryInset));
    root.classList.toggle('poster-preview--gallery-hidden', !truth.galleryVisible);
  }
  if (brandLogoEl) {
    brandLogoEl.src = model.logoSrc || placeholderImages.brandLogo;
  }
  if (brandNameEl) {
    brandNameEl.textContent = model.brandName || 'Brand';
  }
  if (agentNameEl) {
    agentNameEl.textContent = model.agentName || 'Agent';
  }
  if (scenarioImageEl) {
    scenarioImageEl.src = model.scenarioSrc || placeholderImages.scenario;
  }
  if (productImageEl) {
    productImageEl.src = model.productPrimarySrc || placeholderImages.product;
  }
  if (productSecondaryWrapEl) {
    productSecondaryWrapEl.classList.toggle('hidden', !truth.showSecondaryInset || !model.productSecondarySrc);
  }
  if (productSecondaryImageEl) {
    if (truth.showSecondaryInset && model.productSecondarySrc) {
      productSecondaryImageEl.src = model.productSecondarySrc;
    } else {
      productSecondaryImageEl.removeAttribute('src');
    }
  }
  if (titleEl) {
    titleEl.textContent = model.title || 'Title';
  }
  if (subtitleEl) {
    subtitleEl.textContent = model.subtitle || '';
    subtitleEl.classList.toggle('hidden', !truth.subtitleVisible);
  }
  if (featureListEl) {
    renderFeatureTags(featureListEl, model.features);
  }
  if (galleryEl) {
    galleryEl.innerHTML = '';
    galleryEl.classList.toggle('hidden', !truth.galleryVisible);
    if (truth.galleryVisible) {
      model.galleryItems.forEach((entry, index) => {
        const figure = document.createElement('figure');
        figure.dataset.galleryIndex = String(index);
        const img = document.createElement('img');
        img.src = entry?.src || getGalleryPlaceholder(index, galleryPlaceholderLabel);
        img.alt = `${galleryPlaceholderLabel} ${index + 1}`;
        const caption = document.createElement('figcaption');
        caption.textContent = entry?.caption || getModeSDefaultGalleryCaption(index);
        figure.appendChild(img);
        figure.appendChild(caption);
        galleryEl.appendChild(figure);
      });
    }
  }
}

function buildPromptPreview(payload) {
  if (!payload || typeof payload !== 'object') return '';
  const bundle = payload.prompt_bundle || payload.prompts || null;
  const lines = [];
  if (bundle && typeof bundle === 'object') {
    Object.keys(bundle).forEach((slot) => {
      const entry = bundle[slot];
      if (entry == null) return;
      if (typeof entry === 'string') {
        lines.push(`${slot}: ${entry}`);
      } else {
        const preview = entry.prompt || entry.positive || entry.text || '';
        const neg = entry.negative || entry.negative_prompt || '';
        if (preview) lines.push(`${slot}: ${preview}`);
        if (neg) lines.push(`${slot} (negative): ${neg}`);
      }
    });
  }
  if (typeof payload.final_prompt === 'string' && payload.final_prompt.trim()) {
    lines.push(`final_prompt: ${payload.final_prompt.trim()}`);
  }
  return lines.join('\n').trim();
}

function updateDebugPanels({ draft, payload, response } = {}) {
  if (draft !== undefined) {
    stage2State.debugDraft = draft;
    renderJson('debug-draft', draft);
  }
  if (payload !== undefined) {
    stage2State.debugPayload = payload;
    renderJson('debug-payload', payload);
    setText('debug-prompt-preview', buildPromptPreview(payload));
  }
  if (response !== undefined) {
    stage2State.debugResponse = response;
    renderJson('debug-response', response);
  }
}

function bindCopyButton(buttonId, getText) {
  const button = document.getElementById(buttonId);
  if (!button || button.dataset.bound === 'true') return;
  button.dataset.bound = 'true';
  button.addEventListener('click', async () => {
    const text = typeof getText === 'function' ? getText() : '';
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = button.textContent;
      button.textContent = 'Copied';
      setTimeout(() => {
        button.textContent = original || 'Copy';
      }, 1200);
    } catch (error) {
      console.warn('Copy failed', error);
    }
  });
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

function showAssetFallbackWarning(warningEl) {
  if (!warningEl) return;
  warningEl.textContent = 'Fallback asset used.';
  warningEl.classList.remove('hidden');
}

function applyImageWithFallback(imgEl, sources, warningEl) {
  if (!imgEl) return false;
  const candidates = (Array.isArray(sources) ? sources : [sources])
    .map((value) => (typeof value === 'string' ? value.trim() : ''))
    .filter(Boolean);
  if (!candidates.length) return false;

  let index = 0;
  const loadAt = (idx) => {
    const src = candidates[idx];
    if (!src) return;
    imgEl.src = src;
    if (imgEl.style) {
      imgEl.style.visibility = 'visible';
      if (imgEl.style.display === 'none') {
        imgEl.style.display = '';
      }
    }
  };

  imgEl.onerror = () => {
    index += 1;
    if (index < candidates.length) {
      showAssetFallbackWarning(warningEl);
      loadAt(index);
    }
  };
  loadAt(index);
  return true;
}

function setStage2ButtonsDisabled(disabled) {
  const generateButton = document.getElementById('generate-poster');
  const regenerateButton = document.getElementById('regenerate-poster');
  if (generateButton) generateButton.disabled = disabled;
  if (regenerateButton) regenerateButton.disabled = disabled;
}

function setStage2GenerateUiBusy(isBusy) {
  const btnGen = document.getElementById('generate-poster');
  const btnRegen = document.getElementById('regenerate-poster');
  if (btnGen) btnGen.disabled = isBusy;
  if (btnRegen) btnRegen.disabled = isBusy;
}

async function runStage2Generation({ isRegenerate = false } = {}) {
  const now = Date.now();
  if (stage2GenerateInFlight) return;
  if (now - stage2LastClickAt < STAGE2_CLICK_DEBOUNCE_MS) return;
  stage2LastClickAt = now;
  const t0 = Date.now();
  const stage1Snapshot = loadStage1Data() || {};
  stage2State.generationAction = isRegenerate ? 'regenerate' : 'generate';
  stage2State.regenPolicy = isRegenerate
    ? { updateScenario: true, updateGallery: true, updateProduct: false }
    : { updateScenario: false, updateGallery: false, updateProduct: false };

  stage2GenerateInFlight = true;
  setStage2GenerateUiBusy(true);
  try {
    const revealA = (async () => {
      await delay(STAGE2_REVEAL_DELAY_MS);
      renderPosterResult();
    })();

    if (typeof stage2RunGeneration === 'function') {
      await stage2RunGeneration({ isRegenerate });
    }

    await revealA;
    renderPosterResult();
  } finally {
    stage2GenerateInFlight = false;
    setStage2GenerateUiBusy(false);
    const t1 = Date.now();
    const bullets = Array.isArray(stage1Snapshot?.bullets) ? stage1Snapshot.bullets.filter(Boolean) : [];
    const bottomEntries = Array.isArray(stage1Snapshot?.gallery_entries)
      ? stage1Snapshot.gallery_entries.filter((entry) => entry && entry.asset)
      : [];
    console.log({
      bottom_count: bottomEntries.length,
      has_scenario: Boolean(stage1Snapshot?.scenario_asset || stage1Snapshot?.scenario_image),
      has_product2: Boolean(stage1Snapshot?.product_image_2),
      title_len: (stage1Snapshot?.title || '').length,
      bullets_count: bullets.length,
      adjustments: {
        showBullets: stage2State.adjustments?.showBullets !== false,
        titleSize: stage2State.adjustments?.titleSize || 'M',
        fallbackStableClicked: Boolean(stage2State.adjustments?.fallbackStableClicked),
      },
      t0,
      t1,
      duration_ms: t1 - t0,
    });
  }
}

function bindStage2GenerateButtonsOnce() {
  const btnGen = document.getElementById('generate-poster');
  if (!btnGen || btnGen.dataset.bound === '1') return;
  btnGen.dataset.bound = '1';
  const btnRegen = document.getElementById('regenerate-poster');
  if (btnRegen) btnRegen.dataset.bound = '1';

  // Stage2 generate/regenerate handlers (single-flight + debounce)
  btnGen.addEventListener('click', () => void runStage2Generation({ isRegenerate: false }));
  btnRegen?.addEventListener('click', () => void runStage2Generation({ isRegenerate: true }));
}

function rehydrateStage2PosterFromStage1() {
  const snapshot = loadStage1Data() || lastStage1Data || null;
  if (!snapshot) return;
  syncStage2PreviewStateFromStage1(snapshot);
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

const TEXT_SAFE_AREAS = {
  template_dual: {
    title: { x: 0.08, y: 0.68, w: 0.84, h: 0.10, maxLines: 2, baselineFontPx: 40, minFontPx: 18 },
    bullets: { x: 0.08, y: 0.78, w: 0.84, h: 0.14, maxLines: 4, baselineFontPx: 18, minFontPx: 12, lineGap: 4 },
    tagline: { x: 0.10, y: 0.92, w: 0.80, h: 0.05, maxLines: 1, baselineFontPx: 16, minFontPx: 10 },
  },
  template_single: {
    title: { x: 0.08, y: 0.64, w: 0.84, h: 0.12, maxLines: 2, baselineFontPx: 42, minFontPx: 20 },
    bullets: { x: 0.08, y: 0.76, w: 0.84, h: 0.16, maxLines: 4, baselineFontPx: 18, minFontPx: 12, lineGap: 4 },
    tagline: { x: 0.10, y: 0.92, w: 0.80, h: 0.05, maxLines: 1, baselineFontPx: 16, minFontPx: 10 },
  },
};

const TITLE_SCALE_PRESETS = { S: 0.85, M: 1, L: 1.2 };

function applyWireframeLayout(container, templateId) {
  if (!container) return;
  const spec = TEXT_SAFE_AREAS[templateId] || TEXT_SAFE_AREAS.template_dual;
  Object.entries(spec).forEach(([slot, box]) => {
    const el = container.querySelector(`[data-slot="${slot}"]`);
    if (!el) return;
    el.style.left = `${box.x * 100}%`;
    el.style.top = `${box.y * 100}%`;
    el.style.width = `${box.w * 100}%`;
    el.style.height = `${box.h * 100}%`;
  });
}

function fitTextToBox(el, text, config, { scale = 1 } = {}) {
  if (!el || !config) return { didEllipsis: false, fontPx: 0 };
  const baseline = Math.round(config.baselineFontPx * scale);
  const minFontPx = Math.round(config.minFontPx * scale);
  const lineGap = typeof config.lineGap === 'number' ? config.lineGap : 4;
  const content = typeof text === 'string' ? text.trim() : '';
  el.textContent = content;
  el.dataset.ellipsis = '0';

  let fontPx = baseline;
  const applyFont = () => {
    el.style.fontSize = `${fontPx}px`;
    el.style.lineHeight = `${fontPx + lineGap}px`;
  };

  applyFont();
  while (fontPx > minFontPx) {
    if (el.scrollHeight <= el.clientHeight && el.scrollWidth <= el.clientWidth) break;
    fontPx -= 1;
    applyFont();
  }

  let didEllipsis = false;
  if (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth) {
    let trimmed = content;
    while (trimmed.length > 0) {
      trimmed = trimmed.slice(0, -1).trim();
      el.textContent = `${trimmed}\u2026`;
      applyFont();
      if (el.scrollHeight <= el.clientHeight && el.scrollWidth <= el.clientWidth) {
        didEllipsis = true;
        break;
      }
    }
  }

  if (didEllipsis) {
    el.dataset.ellipsis = '1';
  } else {
    el.dataset.ellipsis = '0';
  }
  return { didEllipsis, fontPx };
}

function updateWireframePreview(
  container,
  data,
  templateId,
  warningEl,
  { titleScale = 1, showBullets = true } = {}
) {
  if (!container) return;
  applyWireframeLayout(container, templateId);
  const spec = TEXT_SAFE_AREAS[templateId] || TEXT_SAFE_AREAS.template_dual;
  const titleEl = container.querySelector('[data-slot="title"]');
  const bulletsEl = container.querySelector('[data-slot="bullets"]');
  const taglineEl = container.querySelector('[data-slot="tagline"]');

  const titleText = data?.title || '';
  const bullets = Array.isArray(data?.bullets) ? data.bullets.filter(Boolean) : [];
  const bulletsText = showBullets ? bullets.map((b) => `• ${b}`).join('\n') : '';
  const taglineText = data?.tagline || '';

  const titleFit = fitTextToBox(titleEl, titleText, spec.title, { scale: titleScale });
  const bulletFit = fitTextToBox(bulletsEl, bulletsText, spec.bullets, { scale: 1 });
  const taglineFit = fitTextToBox(taglineEl, taglineText, spec.tagline, { scale: 1 });

  const didEllipsis = titleFit.didEllipsis || bulletFit.didEllipsis || taglineFit.didEllipsis;
  if (warningEl) {
    warningEl.textContent = didEllipsis ? 'Some text was truncated to fit the safe areas.' : '';
  }
}

function ensureGalleryEntries(state, limit = 4) {
  if (!state) return;
  if (!Array.isArray(state.galleryEntries)) {
    state.galleryEntries = [];
  }
  if (typeof limit === 'number' && limit >= 0) {
    state.galleryEntries = state.galleryEntries.slice(0, limit);
  }
}

function updateMaterialPreviewAssets(container, assets = {}, labels = {}) {
  if (!container) return;
  const setSlot = (slotKey, asset, options = {}) => {
    const slot = container.querySelector(`[data-asset-slot="${slotKey}"]`);
    if (!slot) return;
    const img = slot.querySelector('img');
    const placeholder = slot.querySelector('.slot-placeholder');
    const src = pickImageSrc(asset) || '';
    if (img) {
      if (src) {
        img.src = src;
        img.style.display = 'block';
      } else {
        img.removeAttribute('src');
        img.style.display = 'none';
      }
    }
    if (placeholder) {
      placeholder.textContent = src ? (options.filledLabel || 'Ready') : (options.emptyLabel || 'Empty');
    }
    slot.classList.toggle('empty', !src);
  };

  setSlot('scenario', assets.scenario, {
    emptyLabel: labels.scenario || '使用默认场景素材',
  });
  setSlot('product1', assets.product1, {
    emptyLabel: 'Missing',
  });
  setSlot('product2', assets.product2, {
    emptyLabel: 'Empty',
  });

  const bottom = Array.isArray(assets.bottom) ? assets.bottom : [];
  for (let i = 0; i < 4; i += 1) {
    const entry = bottom[i];
    const asset = entry?.asset || entry || null;
    setSlot(`bottom-${i}`, asset, { emptyLabel: 'Empty' });
  }
}

function updateBottomThumbnailsUi(container, state) {
  if (!container || !state) return;
  const entries = Array.isArray(state.galleryEntries) ? state.galleryEntries : [];
  container.querySelectorAll('[data-slot-index]').forEach((slot) => {
    const index = Number(slot.dataset.slotIndex || 0);
    const entry = entries[index];
    const img = slot.querySelector(`[data-bottom-preview="${index}"]`);
    const placeholder = slot.querySelector('.slot-placeholder');
    const src = pickImageSrc(entry?.asset || null) || '';
    if (img) {
      if (src) {
        img.src = src;
        img.style.display = 'block';
      } else {
        img.removeAttribute('src');
        img.style.display = 'none';
      }
    }
    if (placeholder) {
      placeholder.textContent = src ? 'Ready' : 'Empty';
    }
    slot.classList.toggle('empty', !src);
  });
}

function bindModeSBottomThumbnails(container, state, statusElement, refreshPreview) {
  if (!container || !state) return;
  ensureGalleryEntries(state, 4);
  container.querySelectorAll('[data-slot-index]').forEach((slot) => {
    const index = Number(slot.dataset.slotIndex || 0);
    const fileInput = slot.querySelector('input[type="file"]');
    const clearButton = slot.querySelector(`[data-bottom-clear="${index}"]`);

    if (fileInput) {
      fileInput.addEventListener('change', async () => {
        const file = fileInput.files?.[0];
        if (!file) return;
        try {
          const existing = state.galleryEntries[index] || { id: createId(), caption: '' };
          const asset = await prepareAssetFromFile('gallery', file, existing.asset, statusElement);
          state.galleryEntries[index] = { ...existing, asset };
          state.previewBuilt = false;
          updateBottomThumbnailsUi(container, state);
          refreshPreview?.();
        } catch (error) {
          console.error(error);
          setStatus(statusElement, '底部小图处理失败。', 'error');
        } finally {
          fileInput.value = '';
        }
      });
    }

    if (clearButton) {
      clearButton.addEventListener('click', async () => {
        const entry = state.galleryEntries[index];
        if (entry?.asset) {
          await deleteStoredAsset(entry.asset);
        }
        state.galleryEntries[index] = null;
        state.previewBuilt = false;
        updateBottomThumbnailsUi(container, state);
        refreshPreview?.();
      });
    }
  });
}

function bindModeSOptionalAsset(
  input,
  key,
  inlinePreview,
  state,
  refreshPreview,
  statusElement,
  folder = 'uploads'
) {
  if (!input || !state) return;
  const placeholderForKey = (valueKey) => {
    if (valueKey === 'brandLogo') return placeholderImages.brandLogo;
    if (valueKey === 'scenario') return placeholderImages.scenario;
    if (valueKey === 'productImage2') return placeholderImages.productAlt;
    return placeholderImages.product;
  };

  input.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) {
      await deleteStoredAsset(state[key]);
      state[key] = null;
      state.previewBuilt = false;
      if (inlinePreview) {
        inlinePreview.src = placeholderForKey(key);
      }
      refreshPreview?.();
      return;
    }
    try {
      state[key] = await prepareAssetFromFile(folder, file, state[key], statusElement);
      if (inlinePreview) {
        inlinePreview.src = state[key]?.dataUrl || placeholderForKey(key);
      }
      state.previewBuilt = false;
      refreshPreview?.();
    } catch (error) {
      console.error(error);
      setStatus(statusElement, '图片素材处理失败。', 'error');
    }
  });
}
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
      _registryP = fetch(App.utils.assetUrl('templates/registry.json'))
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
// Load .b64 preview files and convert them to data URLs for Image().
async function loadB64AsDataUrl(url, mime = 'image/png') {
  const r = await fetch(url);
  if (!r.ok) throw new Error('无法加载模板预览图资源');
  const b64 = (await r.text()).trim();
  if (b64.startsWith('data:')) return b64;
  return `data:${mime};base64,${b64}`;
}
App.utils.loadImageAny = async (url, mime = 'image/png') => {
  const img = new Image();
  img.decoding = 'async';
  img.crossOrigin = 'anonymous';
  const resolvedUrl = (url && (url.endsWith('.b64') || url.endsWith('.pre')))
    ? await loadB64AsDataUrl(url, mime)
    : url;
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = () => reject(new Error('模板预览图加载失败'));
    img.src = resolvedUrl;
  });
  return img;
};
App.utils.ensureTemplateAssets = (() => {
  const _cache = new Map();
  return async function ensureTemplateAssets(templateId) {
    if (_cache.has(templateId)) return _cache.get(templateId);

    const registry = await App.utils.loadTemplateRegistry();
    const entry = registry.find(i => i.id === templateId) || registry[0];
    if (!entry) throw new Error('模板列表为空');

    // Templates without static preview assets (e.g. Family B) return a spec-less stub.
    if (!entry.spec || !entry.preview) {
      const stub = { entry, spec: null, image: null };
      _cache.set(entry.id, stub);
      return stub;
    }

    const specUrl = App.utils.assetUrl(`templates/${entry.spec}`);
    const imgUrl  = App.utils.assetUrl(`templates/${entry.preview}`);

    const specP = fetch(specUrl).then(r => { if (!r.ok) throw new Error('无法加载模板规范'); return r.json(); });
    const imgP  = App.utils.loadImageAny(imgUrl, 'image/png');

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
    render_mode: state.renderMode || stage2State.renderMode || 'kitposter1_a',
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
  const base = resolveDocumentAssetBase();
  if (!path) return new URL('', base).toString();
  return new URL(path, base).toString();
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

function hasInlineDataUrl(asset) {
  if (!asset) return false;
  const dataUrl = asset.dataUrl || asset.data_url || null;
  return typeof dataUrl == 'string' && dataUrl.startsWith('data:');
}

function hasInlineStage1Assets(stage1Data) {
  if (!stage1Data) return false;
  if (hasInlineDataUrl(stage1Data.brand_logo)) return true;
  if (hasInlineDataUrl(stage1Data.scenario_asset)) return true;
  if (hasInlineDataUrl(stage1Data.product_asset)) return true;
  if (hasInlineDataUrl(stage1Data.product_asset_extra_1)) return true;
  if (hasInlineDataUrl(stage1Data.product_asset_extra_2)) return true;
  if (hasInlineDataUrl(stage1Data.product_image_1)) return true;
  if (hasInlineDataUrl(stage1Data.product_image_2)) return true;
  const entries = Array.isArray(stage1Data.gallery_entries) ? stage1Data.gallery_entries : [];
  return entries.some((entry) => hasInlineDataUrl(entry?.asset));
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

function normaliseStage1ProductCallouts(values) {
  return ensureArray(values)
    .map((value) => (typeof value === 'string' ? value.trim() : ''))
    .filter(Boolean)
    .slice(0, STAGE1_PRODUCT_CALLOUT_MAX_ITEMS);
}

function resolveModeSDefaultText(value, fallbackKey) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (text) return text;
  const fallback = MODE_S_DEFAULT_STAGE1[fallbackKey];
  return typeof fallback === 'string' ? fallback.trim() : '';
}

function resolveStage1ProductCallouts(stage1Data) {
  return normaliseStage1ProductCallouts(
    stage1Data?.product_callouts && stage1Data.product_callouts.length
      ? stage1Data.product_callouts
      : stage1Data?.features && stage1Data.features.length
      ? stage1Data.features
      : stage1Data?.bullets || []
  );
}

function setStage1ProductCalloutInputs(form, values) {
  const inputs = form.querySelectorAll('input[name="product_callouts"]');
  const callouts = normaliseStage1ProductCallouts(values);
  inputs.forEach((input, index) => {
    input.value = callouts[index] ?? '';
  });
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
  add(STAGE2_PROD_API_BASE);

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
    requestId,
    bodyString,
    size,
  };
}

// 完整替换 app.js 里的 postJsonWithRetry
// 发送请求：始终 JSON/UTF-8，支持多基址与重试
// 发送请求：始终 JSON/UTF-8，支持多基址与重试
async function postJsonWithRetry(apiBaseOrBases, path, payload, retry = 1, rawPayload, options = {}) {
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
  const externalSignal = options?.signal || null;

  const throwIfAborted = () => {
    if (externalSignal?.aborted) {
      const abortError = new Error(typeof externalSignal.reason === 'string' ? externalSignal.reason : 'Request aborted');
      abortError.name = 'AbortError';
      throw abortError;
    }
  };

  for (let attempt = 0; attempt <= retry; attempt += 1) {
    throwIfAborted();
    const order = base ? [base, ...bases.filter(x => x !== base)] : bases;

    for (const b of order) {
      throwIfAborted();
      const ctrl = new AbortController();
      const relayAbort = () => ctrl.abort(externalSignal?.reason || 'Request aborted');
      if (externalSignal) {
        if (externalSignal.aborted) {
          relayAbort();
        } else {
          externalSignal.addEventListener('abort', relayAbort, { once: true });
        }
      }
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
        if (e?.name === 'AbortError' && externalSignal?.aborted) {
          throwIfAborted();
        }
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
        if (externalSignal) {
          externalSignal.removeEventListener?.('abort', relayAbort);
        }
        clearTimeout(timer);
      }
    }

    // 整轮失败后：热身 + 等待 + 重选
    throwIfAborted();
    try { await window.warmUp?.(bases, { timeoutMs: 2500 }); } catch {}
    await new Promise(r => setTimeout(r, 800));
    base = await (window.pickHealthyBase?.(bases, { timeoutMs: 2500 })) ?? bases[0];
  }

  throw lastErr || new Error('请求失败');
}

App.utils.postJsonWithRetry = postJsonWithRetry;

async function getJsonWithRetry(apiBaseOrBases, path, retry = 1) {
  const bases = (window.resolveApiBases?.(apiBaseOrBases))
    ?? (Array.isArray(apiBaseOrBases) ? apiBaseOrBases
        : String(apiBaseOrBases || '').split(',').map(s => s.trim()).filter(Boolean));
  if (!bases.length) throw new Error('未配置后端 API 地址');

  const urlFor = (b) => `${String(b).replace(/\/$/, '')}/${String(path).replace(/^\/+/, '')}`;
  let base = await (window.pickHealthyBase?.(bases, { timeoutMs: 2500 })) ?? bases[0];
  let lastErr = null;

  for (let attempt = 0; attempt <= retry; attempt += 1) {
    const order = base ? [base, ...bases.filter(x => x !== base)] : bases;
    for (const b of order) {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const url = urlFor(b);
      try {
        const res = await fetch(url, {
          method: 'GET',
          mode: 'cors',
          cache: 'no-store',
          credentials: 'omit',
          signal: ctrl.signal,
        });
        const text = await res.text();
        let json = null;
        try { json = text ? JSON.parse(text) : null; } catch {}
        if (!res.ok) {
          throw new Error((json && (json.detail || json.message)) || text || `HTTP ${res.status}`);
        }
        return json ?? {};
      } catch (error) {
        lastErr = error;
        base = null;
      } finally {
        clearTimeout(timer);
      }
    }
  }

  throw lastErr || new Error('GET request failed');
}

App.utils.getJsonWithRetry = getJsonWithRetry;


const STORAGE_KEYS = {
  apiBase: 'marketing-poster-api-base',
  stage1: 'marketing-poster-stage1-data',
  stage2: 'marketing-poster-stage2-result',
};
const DRAFT_STORAGE_KEY = 'kitposter:draft';

const LEGACY_DEFAULT_STAGE1 = {
  brand_name: '厨匠ChefCraft',
  agent_name: '星辉渠道服务中心',
  scenario_image: '现代开放式厨房中智能蒸烤一体机的沉浸式体验',
  product_name: 'ChefCraft 智能蒸烤大师',
  channel: 'email',
  intent: 'default',
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

const MODE_S_DEFAULT_STAGE1 = {
  brand_name: 'CUISTANCE',
  agent_name: 'Electric Fryer Series',
  scenario_image: 'default',
  brand_color: '#ef4c54',
  price: '',
  promo: '',
  channel: 'email',
  intent: 'default',
  title: 'Countertop Electric Fryer',
  bullets: [
    'Fast Heating',
    'Precise Temperature Control',
    'Easy-Clean Stainless Steel',
  ],
  product_callouts: [
    'Fast Heating',
    'Precise Temperature Control',
    'Easy-Clean Stainless Steel',
  ],
  subtitle: 'Fast heating, precise control, and durable stainless steel construction for everyday commercial use.',
  tagline: 'Fast heating, precise control, and durable stainless steel construction for everyday commercial use.',
  product_name: '',
  allow_auto_fill: true,
  template_id: 'template_dual',
};
const MODE_S_DEFAULT_BOTTOM_TITLE = 'Power Up Your Fry Station';

const MODE_S_DEFAULT_GALLERY_CAPTIONS = [
  'Basket Detail',
  'Single Tank',
  'Lid Detail',
  'Dual Tank',
];

function getModeSDefaultGalleryCaption(index) {
  return MODE_S_DEFAULT_GALLERY_CAPTIONS[index] || `Series ${index + 1}`;
}

function buildModeSDefaultGalleryEntries(entries = [], limit = 4) {
  const seeded = [];
  for (let index = 0; index < limit; index += 1) {
    const existing = Array.isArray(entries) ? entries[index] : null;
    seeded.push({
      id: existing?.id || createId(),
      caption: (typeof existing?.caption === 'string' && existing.caption.trim()) || getModeSDefaultGalleryCaption(index),
      asset: existing?.asset || null,
      mode: existing?.mode === 'prompt' ? 'prompt' : 'upload',
      prompt: existing?.prompt || null,
    });
  }
  return seeded;
}

function buildModeSFamilyAGalleryFallbackPlan({
  productPrimaryRef,
  productSecondaryRef,
  logoRef,
}) {
  return [
    [productPrimaryRef, productSecondaryRef, logoRef],
    [productSecondaryRef, productPrimaryRef, logoRef],
    [productSecondaryRef, productPrimaryRef, logoRef],
    [productPrimaryRef, productSecondaryRef, logoRef],
  ];
}

const DEFAULT_STAGE1 = MODE_S ? MODE_S_DEFAULT_STAGE1 : LEGACY_DEFAULT_STAGE1;
const AGENT_NAME_PLACEHOLDERS = new Set([
  'email',
  'mail',
  'direct',
  'default',
  'wechat',
  'whatsapp',
  'sms',
  'channel',
  'n/a',
  'na',
]);

function sanitizeAgentName(candidate, brandName = '') {
  const raw = typeof candidate === 'string' ? candidate.trim() : '';
  const brand = typeof brandName === 'string' ? brandName.trim() : '';
  if (raw && !AGENT_NAME_PLACEHOLDERS.has(raw.toLowerCase())) {
    return raw;
  }
  return brand ? `${brand}渠道服务中心` : '渠道服务中心';
}

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
  productAlt: createPlaceholder('产品\\n备用'),
};
const DEFAULT_SCENARIO_ASSET = App.utils.assetUrl('assets/scenes/default.png');
const LOCAL_PLACEHOLDER_IMAGE = App.utils.assetUrl('assets/placeholders/empty.png');

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
  loadBuildInfo();
  loadApiBase();
  void loadBaselineStamps();
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

async function loadBuildInfo() {
  const el = document.getElementById('build-info');
  if (!el) return;
  try {
    const url = assetUrl('build-info.json');
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error('build info unavailable');
    const data = await response.json();
    const commit = (data?.commit || 'local').toString();
    const builtAt = data?.builtAt ? String(data.builtAt) : '';
    el.textContent = builtAt ? `build ${commit} · ${builtAt}` : `build ${commit}`;
  } catch {
    el.textContent = '';
  }
}

function setBaselineStamp(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = value || 'N/A';
}

async function fetchBackendBuildStamp() {
  const candidates = getApiCandidates(apiBaseInput?.value || null);
  for (const base of candidates) {
    const url = joinBasePath(base, '/health');
    if (!url) continue;
    try {
      const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-store',
        credentials: 'omit',
      });
      if (!response.ok) continue;
      const payload = await response.json().catch(() => ({}));
      const stampFromBody = typeof payload?.build_stamp === 'string' ? payload.build_stamp.trim() : '';
      const stampFromHeader = response.headers.get('x-backend-build') || '';
      const stamp = stampFromBody || stampFromHeader;
      if (stamp) return stamp;
    } catch (error) {
      console.warn('[baseline] failed to fetch backend build stamp', base, error);
    }
  }
  return '';
}

async function loadBaselineStamps() {
  setBaselineStamp('frontend-baseline-stamp', FRONTEND_BASELINE_STAMP);
  const backendStamp = await fetchBackendBuildStamp();
  if (backendStamp) {
    const suffix = backendStamp === BACKEND_BASELINE_EXPECTED ? '' : ' (mismatch)';
    setBaselineStamp('backend-baseline-stamp', `${backendStamp}${suffix}`);
    return;
  }
  setBaselineStamp('backend-baseline-stamp', `${BACKEND_BASELINE_EXPECTED} (expected)`);
}

function loadApiBase() {
  if (!apiBaseInput) return;
  const stored = localStorage.getItem(STORAGE_KEYS.apiBase);
  if (stored && !isDeprecatedApiBase(stored)) {
    apiBaseInput.value = stored;
    return;
  }
  if (stored && isDeprecatedApiBase(stored)) {
    localStorage.removeItem(STORAGE_KEYS.apiBase);
  }
  apiBaseInput.value = STAGE2_PROD_API_BASE;
}

function saveApiBase() {
  if (!apiBaseInput) return;
  const value = apiBaseInput.value.trim();
  if (isDeprecatedApiBase(value)) {
    localStorage.removeItem(STORAGE_KEYS.apiBase);
    apiBaseInput.value = STAGE2_PROD_API_BASE;
    return;
  }
  if (value) {
    localStorage.setItem(STORAGE_KEYS.apiBase, value);
  } else {
    localStorage.removeItem(STORAGE_KEYS.apiBase);
  }
}

function initStage1() {
  if (MODE_S) {
    initStage1ModeS();
    return;
  }
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
    productSecondaryImage: document.getElementById('preview-product-secondary-image'),
    productSecondaryWrap: document.getElementById('preview-product-secondary-wrap'),
    featureList: document.getElementById('preview-feature-list'),
    title: document.getElementById('preview-title'),
    subtitle: document.getElementById('preview-subtitle'),
    gallery: document.getElementById('preview-gallery'),
  };

  const inlinePreviews = {
    brand_logo: document.querySelector('[data-inline-preview="brand_logo"]'),
    scenario_asset: document.querySelector('[data-inline-preview="scenario_asset"]'),
    product_asset: document.querySelector('[data-inline-preview="product_asset"]'),
    product_asset_extra_1: document.querySelector('[data-inline-preview="product_asset_extra_1"]'),
    product_asset_extra_2: document.querySelector('[data-inline-preview="product_asset_extra_2"]'),
  };

  const state = {
    brandLogo: null,
    scenario: null,
    product: null,
    productExtra1: null,
    productExtra2: null,
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

  if (MODE_S) {
    state.scenarioMode = 'upload';
    state.productMode = 'upload';
    state.scenarioAllowsPrompt = false;
    state.productAllowsPrompt = false;
    state.galleryAllowsPrompt = false;
  }


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
    if (!img) {
      // No preview image (e.g. Template B / Family B) — draw name placeholder
      ctx.fillStyle = '#e2e8f0';
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = '#64748b';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(assets.entry?.name || templateId, width / 2, height / 2 - 10);
      ctx.font = '11px sans-serif';
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('暂无预览图', width / 2, height / 2 + 12);
    } else {
      const scale = Math.min(width / img.width, height / img.height);
      const dw = img.width * scale;
      const dh = img.height * scale;
      const ox = (width - dw) / 2;
      const oy = (height - dh) / 2;
      ctx.drawImage(img, ox, oy, dw, dh);
    }

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

  attachSingleImageHandler(
    form.querySelector('input[name="product_asset_extra_1"]'),
    'productExtra1',
    inlinePreviews.product_asset_extra_1,
    state,
    refreshPreview,
    statusElement
  );
  attachSingleImageHandler(
    form.querySelector('input[name="product_asset_extra_2"]'),
    'productExtra2',
    inlinePreviews.product_asset_extra_2,
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

function initStage1ModeS() {
  const form = document.getElementById('poster-form');
  const buildPreviewButton = document.getElementById('build-preview');
  const nextButton = document.getElementById('go-to-stage2');
  const statusElement = document.getElementById('stage1-status');
  const previewContainer = document.getElementById('preview-container');
  const layoutStructure = document.getElementById('layout-structure-text');
  const wireframe = document.getElementById('stage1-wireframe');
  const wireframeWarning = document.getElementById('wireframe-warning');
  const bottomThumbnails = document.getElementById('bottom-thumbnails');
  const materialPreviewAssets = document.getElementById('material-preview-assets');
  const brandLogoStatus = document.getElementById('brand-logo-status');
  const templateSelectStage1 = document.getElementById('template-select-stage1');
  const templateVariantStage1 = document.getElementById('template-variant-stage1');
  const templateDescriptionStage1 = document.getElementById('template-description-stage1');
  const templateCanvasStage1 = document.getElementById('template-preview-stage1');
  const stage1FallbackWarning = document.getElementById('stage1-fallback-warning');
  const openPreviewButton = document.getElementById('open-stage1-preview');
  const previewStaleStatus = document.getElementById('preview-stale-status');

  if (!form || !buildPreviewButton || !nextButton) {
    return;
  }

  const previewElements = {
    brandLogo: document.getElementById('preview-brand-logo'),
    brandName: document.getElementById('preview-brand-name'),
    agentName: document.getElementById('preview-agent-name'),
    scenarioImage: document.getElementById('preview-scenario-image'),
    productImage: document.getElementById('preview-product-image'),
    productSecondaryImage: document.getElementById('preview-product-secondary-image'),
    productSecondaryWrap: document.getElementById('preview-product-secondary-wrap'),
    featureList: document.getElementById('preview-feature-list'),
    title: document.getElementById('preview-title'),
    subtitle: document.getElementById('preview-subtitle'),
    gallery: document.getElementById('preview-gallery'),
  };

  const inlinePreviews = {
    brand_logo: document.querySelector('[data-inline-preview="brand_logo"]'),
    scenario_asset: document.querySelector('[data-inline-preview="scenario_asset"]'),
    product_image_1: document.querySelector('[data-inline-preview="product_image_1"]'),
    product_image_2: document.querySelector('[data-inline-preview="product_image_2"]'),
  };

  const state = {
    brandLogo: null,
    scenario: null,
    productImage1: null,
    productImage2: null,
    galleryEntries: buildModeSDefaultGalleryEntries([], 4),
    galleryLimit: 4,
    previewBuilt: false,
    templateId: DEFAULT_STAGE1.template_id,
    templateLabel: '',
    templateVariant: 'a',
    // Template B fields
    skuText: '',
    descriptionTitle: '',
    descriptionBody: '',
    materialsImages: [],
  };

  let currentLayoutPreview = '';
  let templateRegistry = [];
  const previewGate = {
    open: false,
    stale: true,
  };

  const updateBrandLogoStatus = () => {
    if (!brandLogoStatus) return;
    const url = state.brandLogo?.remoteUrl || state.brandLogo?.url || '';
    const key = state.brandLogo?.r2Key || '';
    if (url) {
      brandLogoStatus.textContent = `Logo URL: ${url}`;
    } else if (key) {
      brandLogoStatus.textContent = `Logo URL: ${key}`;
    } else {
      brandLogoStatus.textContent = 'Logo URL: 尚未上传';
    }
  };

  const refreshPreview = () => {
    if (!form) return null;
    if (stage1FallbackWarning) {
      stage1FallbackWarning.textContent = '';
      stage1FallbackWarning.classList.add('hidden');
    }

    const payload = collectStage1Data(form, state, { strict: false });
    const layoutPreview = buildLayoutPreview(payload);
    if (layoutStructure) {
      layoutStructure.textContent = layoutPreview;
    }

    updateWireframePreview(
      wireframe,
      {
        title: payload.title || '',
        bullets: payload.bullets || [],
        tagline: payload.tagline || payload.promo || '',
      },
      state.templateId || DEFAULT_STAGE1.template_id,
      wireframeWarning
    );

    const scenarioLabel = payload.scenario_image && payload.scenario_image !== 'default'
      ? `Scenario: ${payload.scenario_image}`
      : '使用默认场景素材';
    updateMaterialPreviewAssets(
      materialPreviewAssets,
      {
        scenario: state.scenario,
        product1: state.productImage1,
        product2: state.productImage2,
        bottom: state.galleryEntries,
      },
      { scenario: scenarioLabel }
    );
    updateBottomThumbnailsUi(bottomThumbnails, state);
    updateBrandLogoStatus();

    const previewPayload = {
      ...payload,
      features: payload.product_callouts || payload.features || payload.bullets || [],
      subtitle: payload.subtitle || payload.tagline || payload.promo || '',
      brand_logo: payload.brand_logo,
      scenario_asset: payload.scenario_asset,
      product_asset: payload.product_asset || payload.product_image_1,
      gallery_entries: payload.gallery_entries || [],
    };
    currentLayoutPreview = updatePosterPreview(
      previewPayload,
      state,
      previewElements,
      layoutStructure,
      previewContainer
    );

    if (previewElements.brandLogo) {
      applyImageWithFallback(
        previewElements.brandLogo,
        [pickImageSrc(state.brandLogo), LOCAL_PLACEHOLDER_IMAGE, placeholderImages.brandLogo],
        stage1FallbackWarning
      );
    }
    if (previewElements.scenarioImage) {
      applyImageWithFallback(
        previewElements.scenarioImage,
        [
          pickImageSrc(state.scenario),
          DEFAULT_SCENARIO_ASSET,
          LOCAL_PLACEHOLDER_IMAGE,
          placeholderImages.scenario,
        ],
        stage1FallbackWarning
      );
    }
    if (previewElements.productImage) {
      applyImageWithFallback(
        previewElements.productImage,
        [pickImageSrc(state.productImage1), LOCAL_PLACEHOLDER_IMAGE, placeholderImages.product],
        stage1FallbackWarning
      );
    }

    return payload;
  };

  const updatePreviewGateUi = () => {
    if (previewContainer) {
      previewContainer.classList.toggle('hidden', !previewGate.open);
    }
    if (openPreviewButton) {
      openPreviewButton.textContent = previewGate.open ? 'Refresh Preview' : 'Open Preview';
      openPreviewButton.setAttribute('aria-expanded', previewGate.open ? 'true' : 'false');
    }
    if (previewStaleStatus) {
      if (!previewGate.open) {
        previewStaleStatus.textContent = previewGate.stale
          ? '预览已收起，打开后会按最新输入重新渲染。'
          : '预览已收起。';
      } else {
        previewStaleStatus.textContent = previewGate.stale
          ? '预览可能不是最新，请在需要时刷新。'
          : '预览已是最新。';
      }
    }
  };

  const markPreviewStale = () => {
    previewGate.stale = true;
    updatePreviewGateUi();
  };

  const requestPreviewUpdate = () => {
    markPreviewStale();
    return null;
  };

  const openPreviewOnDemand = () => {
    previewGate.open = true;
    const payload = refreshPreview();
    previewGate.stale = false;
    updatePreviewGateUi();
    return payload;
  };

  updatePreviewGateUi();

  const stored = loadStage1Data();
  if (stored) {
    void (async () => {
      await applyStage1DataToForm(stored, form, state, inlinePreviews);
      state.galleryEntries = buildModeSDefaultGalleryEntries(state.galleryEntries, 4);
      state.previewBuilt = Boolean(stored.preview_built);
      if (layoutStructure && stored.layout_preview) {
        layoutStructure.textContent = stored.layout_preview;
      }
      if (templateVariantStage1) {
        templateVariantStage1.value = state.templateVariant || 'a';
      }
      applyVariantFieldVisibility(state.templateVariant || 'a');
      updateStage1TemplateVariantLabels(state.templateVariant || 'a');
      refreshVariantTemplateMeta(state.templateVariant || 'a');
      renderMaterialsSlots();
      markPreviewStale();
    })();
  } else {
    applyStage1Defaults(form);
    state.galleryEntries = buildModeSDefaultGalleryEntries(state.galleryEntries, 4);
    updateInlinePlaceholders(inlinePreviews);
    updateStage1TemplateVariantLabels(state.templateVariant || 'a');
    markPreviewStale();
  }

  const refreshTemplatePreviewStage1 = async (templateId) => {
    if (!templateCanvasStage1) return;
    try {
      const assets = await App.utils.ensureTemplateAssets(templateId);
      const ctx = templateCanvasStage1.getContext('2d');
      if (!ctx) return;
      const { width, height } = templateCanvasStage1;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#f8fafc';
      ctx.fillRect(0, 0, width, height);
      if (assets.image) {
        const img = assets.image;
        const scale = Math.min(width / img.width, height / img.height);
        const dw = img.width * scale;
        const dh = img.height * scale;
        const ox = (width - dw) / 2;
        const oy = (height - dh) / 2;
        ctx.drawImage(img, ox, oy, dw, dh);
      } else {
        // No preview image — draw placeholder text on canvas
        ctx.fillStyle = '#e2e8f0';
        ctx.fillRect(0, 0, width, height);
        ctx.fillStyle = '#64748b';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(assets.entry?.name || templateId, width / 2, height / 2 - 10);
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('暂无预览图', width / 2, height / 2 + 12);
      }
      if (templateDescriptionStage1) {
        templateDescriptionStage1.textContent = assets.entry?.description || '';
      }
    } catch (error) {
      console.error('[template preview] failed', error);
      if (templateDescriptionStage1) {
        templateDescriptionStage1.textContent = '模板预览加载失败，请检查 templates 资源。';
      }
    }
  };

  const mountTemplateChooserStage1 = async () => {
    if (!templateSelectStage1) return;
    try {
      templateRegistry = await App.utils.loadTemplateRegistry();
    } catch (error) {
      console.error('[registry] load failed', error);
      setStatus(statusElement, '无法加载模板列表，请检查 templates/registry.json。', 'warning');
      return;
    }
    if (!Array.isArray(templateRegistry) || templateRegistry.length === 0) {
      setStatus(statusElement, '模板列表为空，请确认 templates/registry.json。', 'warning');
      return;
    }

    templateSelectStage1.innerHTML = '';
    templateRegistry.forEach((entry) => {
      const option = document.createElement('option');
      option.value = entry.id;
      option.textContent = entry.name || entry.id;
      templateSelectStage1.appendChild(option);
    });

    const storedData = loadStage1Data();
    if (storedData?.template_id) {
      state.templateId = storedData.template_id;
      state.templateLabel = storedData.template_label || '';
    } else if (templateRegistry[0]) {
      state.templateId = templateRegistry[0].id;
      state.templateLabel = templateRegistry[0].name || '';
    }
    templateSelectStage1.value = state.templateId;

    if (templateVariantStage1) {
      templateVariantStage1.value = state.templateVariant || 'a';
    }

    await refreshTemplatePreviewStage1(state.templateId);

    templateSelectStage1.addEventListener('change', async (event) => {
      const value = event.target.value || DEFAULT_STAGE1.template_id;
      state.templateId = value;
      const entry = templateRegistry.find((item) => item.id === value);
      state.templateLabel = entry?.name || '';
      state.previewBuilt = false;
      requestPreviewUpdate();
      await refreshTemplatePreviewStage1(value);
    });
  };

  void mountTemplateChooserStage1();

  function applyVariantFieldVisibility(variant) {
    document.querySelectorAll('[data-variant-visible]').forEach((el) => {
      const v = el.dataset.variantVisible;
      el.hidden = v !== 'all' && v !== variant;
    });
    // Template selector is only meaningful for Variant A (single B template exists)
    if (templateSelectStage1) {
      templateSelectStage1.closest('label')
        ? (templateSelectStage1.closest('label').hidden = variant === 'b')
        : (templateSelectStage1.hidden = variant === 'b');
    }
  }

  function updateStage1TemplateVariantLabels(variant) {
    const subtitleLabel = document.getElementById('stage1-subtitle-label');
    const subtitleHint = document.getElementById('stage1-subtitle-hint');
    const coreAssetsLegend = document.getElementById('stage1-core-assets-legend');
    const product1Label = document.getElementById('stage1-product1-label');
    const product1Hint = document.getElementById('stage1-product1-hint');
    const product2Label = document.getElementById('stage1-product2-label');
    const product2Hint = document.getElementById('stage1-product2-hint');
    const productDescLabel = document.getElementById('stage1-product-desc-label');
    const materialsLabel = document.getElementById('stage1-materials-label');
    const materialsHint = document.getElementById('stage1-materials-hint');
    const secondaryClearButton = document.querySelector('[data-secondary-image-clear]');
    if (subtitleLabel) {
      subtitleLabel.textContent = variant === 'b'
        ? 'Subtitle / Secondary Heading (optional)'
        : 'Bottom Support Copy (optional)';
    }
    if (subtitleHint) {
      subtitleHint.textContent = variant === 'b'
        ? 'Template B 中该文案留在顶部标题/副标题/SKU 区，不进入产品标注卖点。'
        : '该文案属于底部区域，不进入产品标注卖点。';
    }
    if (coreAssetsLegend) {
      coreAssetsLegend.textContent = variant === 'b' ? 'Product Assets' : 'Core Assets';
    }
    if (product1Label) {
      product1Label.textContent = variant === 'b' ? 'Primary product image (required)' : 'Product image 1 (required)';
    }
    if (product1Hint) {
      product1Hint.textContent = variant === 'b'
        ? '主图录产品图；请保持产品独立、不要变形。'
        : '请使用清晰产品图，干净背景更稳定。';
    }
    if (product2Label) {
      product2Label.textContent = variant === 'b' ? 'Supporting detail image (optional)' : 'Product image 2 (optional)';
    }
    if (product2Hint) {
      product2Hint.textContent = variant === 'b'
        ? '可选细节或辅助角度图；只辅助主图，不与主图竞争。'
        : '可选第二角度或细节图。';
    }
    if (secondaryClearButton) {
      secondaryClearButton.textContent = variant === 'b' ? 'Clear supporting detail' : 'Clear secondary image';
    }
    if (productDescLabel) {
      productDescLabel.textContent = variant === 'b' ? 'Product reference line' : 'Product description';
    }
    if (materialsLabel) {
      materialsLabel.innerHTML = variant === 'b'
        ? '配件 / 刀头 / 材质辅图 <span class="optional">(选填，最多 5 张)</span>'
        : '材质 / 配料图片 <span class="optional">(选填，最多 5 张)</span>';
    }
    if (materialsHint) {
      materialsHint.textContent = variant === 'b'
        ? '这些素材作为产品主图下方的辅助证据条，不是第二主视觉。'
        : '产品材质、配料或细节图，显示在产品主图下方的缩略图条。';
    }
  }

  function refreshVariantTemplateMeta(variant) {
    const effectiveId =
      variant === 'b' ? 'template_product_sheet_v1' : state.templateId;
    void refreshTemplatePreviewStage1(effectiveId);
  }

  if (templateVariantStage1) {
    templateVariantStage1.addEventListener('change', () => {
      state.templateVariant = templateVariantStage1.value || 'a';
      state.previewBuilt = false;
      applyVariantFieldVisibility(state.templateVariant);
      updateStage1TemplateVariantLabels(state.templateVariant);
      refreshVariantTemplateMeta(state.templateVariant);
      requestPreviewUpdate();
    });
  }

  ensureGalleryEntries(state, 4);
  bindModeSBottomThumbnails(bottomThumbnails, state, statusElement, requestPreviewUpdate);

  // ── Template B: materials image slots ──────────────────────────────────────
  const MATERIALS_MAX = 5;
  const materialsSlotContainer = document.getElementById('materials-image-slots');
  const addMaterialsBtn = document.getElementById('add-materials-image-btn');

  const renderMaterialsSlots = () => {
    if (!materialsSlotContainer) return;
    materialsSlotContainer.innerHTML = '';
    state.materialsImages.forEach((entry, idx) => {
      const slot = document.createElement('div');
      slot.className = 'thumbnail-slot';
      slot.dataset.materialsIndex = idx;

      const preview = document.createElement('div');
      preview.className = 'thumbnail-preview';
      const img = document.createElement('img');
      img.alt = `材质图片 ${idx + 1}`;
      if (entry.url) {
        img.src = entry.dataUrl || entry.url;
      }
      const placeholder = document.createElement('span');
      placeholder.className = 'slot-placeholder';
      placeholder.textContent = '未上传';
      preview.appendChild(img);
      preview.appendChild(placeholder);

      const actions = document.createElement('div');
      actions.className = 'thumbnail-actions';
      const uploadLabel = document.createElement('label');
      uploadLabel.className = 'button-like';
      uploadLabel.textContent = entry.url ? '替换' : '上传';
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = 'image/*';
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
          state.materialsImages[idx] = { file, url: ev.target.result, dataUrl: ev.target.result, key: null };
          renderMaterialsSlots();
          state.previewBuilt = false;
          markPreviewStale();
        };
        reader.readAsDataURL(file);
      });
      uploadLabel.appendChild(fileInput);

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'secondary';
      removeBtn.textContent = '移除';
      removeBtn.addEventListener('click', () => {
        state.materialsImages.splice(idx, 1);
        renderMaterialsSlots();
        state.previewBuilt = false;
        markPreviewStale();
        if (addMaterialsBtn) {
          addMaterialsBtn.disabled = state.materialsImages.length >= MATERIALS_MAX;
        }
      });

      actions.appendChild(uploadLabel);
      actions.appendChild(removeBtn);
      slot.appendChild(preview);
      slot.appendChild(actions);
      materialsSlotContainer.appendChild(slot);
    });

    if (addMaterialsBtn) {
      addMaterialsBtn.disabled = state.materialsImages.length >= MATERIALS_MAX;
    }
  };

  if (addMaterialsBtn) {
    addMaterialsBtn.addEventListener('click', () => {
      if (state.materialsImages.length >= MATERIALS_MAX) return;
      state.materialsImages.push({ file: null, url: null, dataUrl: null, key: null });
      renderMaterialsSlots();
      state.previewBuilt = false;
      markPreviewStale();
    });
  }

  renderMaterialsSlots();
  updateStage1TemplateVariantLabels(state.templateVariant || 'a');
  // ── end materials slots ────────────────────────────────────────────────────

  attachSingleImageHandler(
    form.querySelector('input[name="product_image_1"]'),
    'productImage1',
    inlinePreviews.product_image_1,
    state,
    requestPreviewUpdate,
    statusElement
  );

  attachSingleImageHandler(
    form.querySelector('input[name="product_image_2"]'),
    'productImage2',
    inlinePreviews.product_image_2,
    state,
    requestPreviewUpdate,
    statusElement
  );
  bindStage1SecondaryImageClearButton(
    document.querySelector('[data-secondary-image-clear]'),
    form.querySelector('input[name="product_image_2"]'),
    inlinePreviews.product_image_2,
    state,
    requestPreviewUpdate,
    statusElement
  );

  bindModeSOptionalAsset(
    form.querySelector('input[name="brand_logo"]'),
    'brandLogo',
    inlinePreviews.brand_logo,
    state,
    requestPreviewUpdate,
    statusElement,
    'brand-logo'
  );

  bindModeSOptionalAsset(
    form.querySelector('input[name="scenario_asset"]'),
    'scenario',
    inlinePreviews.scenario_asset,
    state,
    requestPreviewUpdate,
    statusElement,
    'scenario'
  );

  form.addEventListener('input', () => {
    state.previewBuilt = false;
    // Keep Template B text state in sync
    const skuEl = document.getElementById('sku-text-stage1');
    if (skuEl) state.skuText = skuEl.value.trim();
    const descTitleEl = document.getElementById('description-title-stage1');
    if (descTitleEl) state.descriptionTitle = descTitleEl.value.trim();
    const descBodyEl = document.getElementById('description-body-stage1');
    if (descBodyEl) state.descriptionBody = descBodyEl.value.trim();
    requestPreviewUpdate();
  });

  const persist = (payload, previewBuilt) => {
    const layoutPreview = currentLayoutPreview || buildLayoutPreview(payload);
    const serialised = serialiseStage1Data(payload, state, layoutPreview, previewBuilt);
    saveStage1Data(serialised);
    if (layoutStructure) {
      layoutStructure.textContent = layoutPreview;
    }
  };

  buildPreviewButton.addEventListener('click', () => {
    const relaxedPayload = collectStage1Data(form, state, { strict: false });
    openPreviewOnDemand();
    try {
      const strictPayload = collectStage1Data(form, state, { strict: true });
      state.previewBuilt = true;
      persist(strictPayload, true);
      setStatus(statusElement, '版式预览已构建，可继续下一环节。', 'success');
    } catch (error) {
      state.previewBuilt = false;
      persist(relaxedPayload, false);
      const reason = error?.message || '请补全必填素材。';
      setStatus(statusElement, reason, 'warning');
    }
  });

  if (openPreviewButton) {
    openPreviewButton.addEventListener('click', () => {
      try {
        openPreviewOnDemand();
        setStatus(statusElement, '已按需渲染预览。', 'info');
      } catch (error) {
        console.error(error);
        setStatus(statusElement, error.message || '预览渲染失败。', 'error');
      }
    });
  }

  nextButton.addEventListener('click', () => {
    try {
      const payload = collectStage1Data(form, state, { strict: true });
      state.previewBuilt = true;
      persist(payload, true);
      setStatus(statusElement, '素材已保存，正在跳转至环节 2。', 'info');
      window.location.href = 'stage2.html';
    } catch (error) {
      setStatus(statusElement, error.message || '请先完成版式预览后再继续。', 'error');
    }
  });
}

function applyStage1Defaults(form) {
  if (MODE_S) {
    for (const [key, value] of Object.entries(DEFAULT_STAGE1)) {
      const element = form.elements.namedItem(key);
      if (element && typeof value === 'string') {
        element.value = value;
      }
    }

    setStage1ProductCalloutInputs(form, DEFAULT_STAGE1.product_callouts || DEFAULT_STAGE1.bullets || []);
    const allowAutoFill = form.elements.namedItem('allow_auto_fill');
    if (allowAutoFill && 'checked' in allowAutoFill) {
      allowAutoFill.checked = DEFAULT_STAGE1.allow_auto_fill !== false;
    }
    const templateVariant = form.elements.namedItem('template_variant');
    if (templateVariant && 'value' in templateVariant) {
      templateVariant.value = 'a';
    }
    return;
  }

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

  if (MODE_S) {
    scenarioModeInputs.forEach((input) => {
      input.checked = input.value === 'upload';
      input.disabled = input.value === 'prompt';
    });
    productModeInputs.forEach((input) => {
      input.checked = input.value === 'upload';
      input.disabled = input.value === 'prompt';
    });
  }

  const productPrompt = form.elements.namedItem('product_prompt');
  if (productPrompt && 'value' in productPrompt) {
    productPrompt.value = '';
  }
}

function updateInlinePlaceholders(inlinePreviews) {
  if (inlinePreviews.brand_logo) inlinePreviews.brand_logo.src = placeholderImages.brandLogo;
  if (inlinePreviews.scenario_asset) inlinePreviews.scenario_asset.src = placeholderImages.scenario;
  if (inlinePreviews.product_asset) inlinePreviews.product_asset.src = placeholderImages.product;
  if (inlinePreviews.product_asset_extra_1) inlinePreviews.product_asset_extra_1.src = placeholderImages.product;
  if (inlinePreviews.product_asset_extra_2) inlinePreviews.product_asset_extra_2.src = placeholderImages.product;
  if (inlinePreviews.product_image_1) inlinePreviews.product_image_1.src = placeholderImages.product;
  if (inlinePreviews.product_image_2) inlinePreviews.product_image_2.src = placeholderImages.productAlt;
}

async function applyStage1DataToForm(data, form, state, inlinePreviews) {
  if (MODE_S) {
    for (const key of [
      'brand_name',
      'agent_name',
      'brand_color',
      'price',
      'promo',
      'channel',
      'intent',
      'title',
      'subtitle',
      'scenario_image',
      'product_name',
    ]) {
      const element = form.elements.namedItem(key);
      const nextValue =
        typeof data[key] === 'string'
          ? (data[key].trim() || (typeof DEFAULT_STAGE1[key] === 'string' ? DEFAULT_STAGE1[key] : ''))
          : key === 'subtitle' && typeof data.tagline === 'string'
          ? (data.tagline.trim() || DEFAULT_STAGE1.subtitle || '')
          : '';
      if (element && typeof nextValue === 'string') {
        element.value = nextValue;
      }
    }

    const allowAutoFill = form.elements.namedItem('allow_auto_fill');
    if (allowAutoFill && 'checked' in allowAutoFill) {
      allowAutoFill.checked = data.allow_auto_fill !== false;
    }

    setStage1ProductCalloutInputs(
      form,
      resolveStage1ProductCallouts(data).length
        ? resolveStage1ProductCallouts(data)
        : DEFAULT_STAGE1.product_callouts || DEFAULT_STAGE1.bullets || []
    );

    state.brandLogo = await rehydrateStoredAsset(data.brand_logo);
    state.scenario = await rehydrateStoredAsset(data.scenario_asset);
    state.productImage1 = await rehydrateStoredAsset(data.product_image_1);
    state.productImage2 = await rehydrateStoredAsset(data.product_image_2);
      const storedGallery = Array.isArray(data.gallery_entries)
        ? data.gallery_entries.filter(Boolean)
        : [];
      state.galleryEntries = await Promise.all(
        storedGallery.map(async (entry) => ({
          id: entry.id || createId(),
          caption: entry.caption || '',
          asset: await rehydrateStoredAsset(entry.asset),
          mode: 'upload',
          prompt: null,
        }))
      );
      state.galleryEntries = buildModeSDefaultGalleryEntries(state.galleryEntries, 4);
      ensureGalleryEntries(state, 4);
    state.templateId = data.template_id || DEFAULT_STAGE1.template_id;
    state.templateLabel = data.template_label || '';
    state.templateVariant = data.template_variant || 'a';

    // Template B text fields
    state.skuText = data.sku_text || '';
    state.descriptionTitle = data.description_title || '';
    state.descriptionBody = data.description_body || '';
    const skuInput = document.getElementById('sku-text-stage1');
    if (skuInput) skuInput.value = state.skuText;
    const descTitleInput = document.getElementById('description-title-stage1');
    if (descTitleInput) descTitleInput.value = state.descriptionTitle;
    const descBodyInput = document.getElementById('description-body-stage1');
    if (descBodyInput) descBodyInput.value = state.descriptionBody;

    // Template B materials images
    state.materialsImages = Array.isArray(data.materials_images)
      ? data.materials_images.map((e) => ({ file: null, url: e.url || null, dataUrl: e.url || null, key: e.key || null }))
      : [];

    if (inlinePreviews.brand_logo) {
      inlinePreviews.brand_logo.src =
        state.brandLogo?.dataUrl || placeholderImages.brandLogo;
    }
    if (inlinePreviews.scenario_asset) {
      inlinePreviews.scenario_asset.src =
        state.scenario?.dataUrl || placeholderImages.scenario;
    }
    if (inlinePreviews.product_image_1) {
      inlinePreviews.product_image_1.src =
        state.productImage1?.dataUrl || placeholderImages.product;
    }
    if (inlinePreviews.product_image_2) {
      inlinePreviews.product_image_2.src =
        state.productImage2?.dataUrl || placeholderImages.productAlt;
    }
    return;
  }

  for (const key of ['brand_name', 'agent_name', 'scenario_image', 'product_name', 'channel', 'intent', 'title', 'subtitle']) {
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
  if (MODE_S) {
    state.scenarioMode = 'upload';
    state.productMode = 'upload';
  }

  const scenarioModeInputs = form.querySelectorAll('input[name="scenario_mode"]');
  scenarioModeInputs.forEach((input) => {
    input.checked = input.value === scenarioModeValue;
  });

  const productModeInputs = form.querySelectorAll('input[name="product_mode"]');
  productModeInputs.forEach((input) => {
    input.checked = input.value === productModeValue;
  });

  if (MODE_S) {
    scenarioModeInputs.forEach((input) => {
      input.checked = input.value === 'upload';
      input.disabled = input.value === 'prompt';
    });
    productModeInputs.forEach((input) => {
      input.checked = input.value === 'upload';
      input.disabled = input.value === 'prompt';
    });
  }

  const productPrompt = form.elements.namedItem('product_prompt');
  if (productPrompt && 'value' in productPrompt) {
    productPrompt.value =
      typeof data.product_prompt === 'string' ? data.product_prompt : '';
  }

  state.brandLogo = await rehydrateStoredAsset(data.brand_logo);
  updateMaterialUrlDisplay('brand_logo', state.brandLogo);
  state.scenario = await rehydrateStoredAsset(data.scenario_asset);
  state.product = await rehydrateStoredAsset(data.product_asset);
  state.productExtra1 = await rehydrateStoredAsset(data.product_asset_extra_1);
  state.productExtra2 = await rehydrateStoredAsset(data.product_asset_extra_2);
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
  if (inlinePreviews.product_asset_extra_1) {
    inlinePreviews.product_asset_extra_1.src = state.productExtra1?.dataUrl || placeholderImages.product;
  }
  if (inlinePreviews.product_asset_extra_2) {
    inlinePreviews.product_asset_extra_2.src = state.productExtra2?.dataUrl || placeholderImages.product;
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
  const placeholderForKey = (valueKey) => {
    if (valueKey === 'brandLogo') return placeholderImages.brandLogo;
    if (valueKey === 'scenario') return placeholderImages.scenario;
    if (valueKey === 'productImage2') return placeholderImages.productAlt;
    return placeholderImages.product;
  };
  input.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) {
      await deleteStoredAsset(state[key]);
      state[key] = null;
      state.previewBuilt = false;
      if (inlinePreview) {
        inlinePreview.src = placeholderForKey(key);
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
        productExtra1: 'product',
        productExtra2: 'product',
        productImage1: 'product',
        productImage2: 'product',
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
        inlinePreview.src = state[key]?.dataUrl || placeholderForKey(key);
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

function bindStage1SecondaryImageClearButton(
  button,
  input,
  inlinePreview,
  state,
  refreshPreview,
  statusElement
) {
  if (!button) return;
  button.addEventListener('click', async () => {
    try {
      await deleteStoredAsset(state.productImage2);
      state.productImage2 = null;
      state.previewBuilt = false;
      if (input) {
        input.value = '';
      }
      if (inlinePreview) {
        inlinePreview.src = placeholderImages.productAlt;
      }
      refreshPreview?.();
      setStatus(statusElement, '第二产品图已清除。', 'info');
    } catch (error) {
      console.error(error);
      setStatus(statusElement, '清除第二产品图失败。', 'error');
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
    const promptTextarea = document.createElement('textArea');
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
function buildModeSGalleryEntries(state) {
  return [];
}

function collectStage1Data(form, state, { strict = false } = {}) {
  const formData = new FormData(form);
  if (MODE_S) {
    const rawProductCallouts = normaliseStage1ProductCallouts(
      formData.getAll('product_callouts').map((value) => value.toString())
    );
    const productCallouts = rawProductCallouts.length
      ? rawProductCallouts
      : [...(DEFAULT_STAGE1.product_callouts || DEFAULT_STAGE1.bullets || [])];

    const channel =
      formData.get('channel')?.toString().trim() || MODE_S_DEFAULT_STAGE1.channel || '';
    const intent =
      formData.get('intent')?.toString().trim() || MODE_S_DEFAULT_STAGE1.intent || '';
      const modeSGalleryEntries = buildModeSDefaultGalleryEntries(state.galleryEntries, 4);
      state.galleryEntries = modeSGalleryEntries;
      const modeSBrandName = resolveModeSDefaultText(formData.get('brand_name')?.toString(), 'brand_name');
      const modeSAgentName = resolveModeSAgentName(
        resolveModeSDefaultText(formData.get('agent_name')?.toString(), 'agent_name'),
        modeSBrandName
      );
      const payload = {
        brand_name: modeSBrandName,
        agent_name: modeSAgentName,
        brand_color: formData.get('brand_color')?.toString().trim() || '',
        price: formData.get('price')?.toString().trim() || '',
      promo: formData.get('promo')?.toString().trim() || '',
      channel,
      intent,
      scenario_image:
        formData.get('scenario_image')?.toString().trim() ||
        MODE_S_DEFAULT_STAGE1.scenario_image ||
        'default',
      product_name: formData.get('product_name')?.toString().trim() || '',
      title: resolveModeSDefaultText(formData.get('title')?.toString(), 'title'),
      subtitle: resolveModeSDefaultText(formData.get('subtitle')?.toString(), 'subtitle'),
      tagline: resolveModeSDefaultText(formData.get('subtitle')?.toString(), 'subtitle'),
      allow_auto_fill: formData.get('allow_auto_fill') === 'on',
      product_callouts: productCallouts,
      bullets: productCallouts,
      features: productCallouts,
      brand_logo: state.brandLogo || null,
      scenario_asset: state.scenario || null,
        product_asset: state.productImage1 || null,
        product_image_1: state.productImage1,
        product_image_2: state.productImage2,
        gallery_entries: modeSGalleryEntries.map((entry, index) => ({
          id: entry.id,
          caption: entry.caption || getModeSDefaultGalleryCaption(index),
          asset: entry.asset || null,
          mode: 'upload',
          prompt: null,
        })),
        template_id: state.templateId || DEFAULT_STAGE1.template_id,
        template_variant: formData.get('template_variant')?.toString().trim() || 'a',
      };

    // Template B field overlay
    const activeVariant = payload.template_variant;
    if (activeVariant === 'b') {
      payload.template_id = 'template_product_sheet_v1';
      payload.sku_text = form.querySelector('[name="sku_text"]')?.value?.trim() || null;
      payload.description_title = form.querySelector('[name="description_title"]')?.value?.trim() || null;
      payload.description_body = form.querySelector('[name="description_body"]')?.value?.trim() || null;
      payload.materials_images = state.materialsImages
        .filter((e) => e.url)
        .map((e) => ({ url: e.url, key: e.key || null }));
    }

    if (strict) {
      if (!payload.product_image_1) {
        throw new Error('Product image 1 is required.');
      }
      if (!payload.title) {
        throw new Error('Title is required.');
      }
      if (productCallouts.length > STAGE1_PRODUCT_CALLOUT_MAX_ITEMS) {
        throw new Error(`Please keep product callouts to ${STAGE1_PRODUCT_CALLOUT_MAX_ITEMS} or fewer.`);
      }
    }

    return payload;
  }

  const payload = {
    brand_name: formData.get('brand_name')?.toString().trim() || '',
    agent_name: formData.get('agent_name')?.toString().trim() || '',
    scenario_image: formData.get('scenario_image')?.toString().trim() || '',
    product_name: formData.get('product_name')?.toString().trim() || '',
    channel: formData.get('channel')?.toString().trim() || '',
    intent: formData.get('intent')?.toString().trim() || '',
    title: formData.get('title')?.toString().trim() || '',
    subtitle: formData.get('subtitle')?.toString().trim() || '',
  };

  const features = formData
    .getAll('features')
    .map((feature) => feature.toString().trim())
    .filter((feature) => feature.length > 0);

  payload.features = features;

  const galleryLimit = MODE_S ? 0 : (state.galleryLimit || 4);
  const galleryLabel = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;

  const galleryEntries = MODE_S
    ? buildModeSGalleryEntries(state)
    : state.galleryEntries.slice(0, galleryLimit).map((entry) => ({
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
  payload.scenario_mode = MODE_S ? 'upload' : state.scenarioMode || 'upload';
  payload.product_mode = MODE_S ? 'upload' : state.productMode || 'upload';
  if (MODE_S) {
    payload.product_prompt = null;
    payload.scenario_prompt = null;
  } else {
    const productPromptValue = formData.get('product_prompt')?.toString().trim() || '';
    payload.product_prompt = productPromptValue || null;
    payload.scenario_prompt =
      payload.scenario_mode === 'prompt' ? payload.scenario_image : null;
  }
  payload.gallery_label = galleryLabel;
  payload.gallery_limit = galleryLimit;
  payload.gallery_allows_prompt = MODE_S ? false : state.galleryAllowsPrompt !== false;

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
      if (MODE_S && key == 'scenario_image') {
        continue;
      }
      if (typeof value === 'string' && !value) {
        missing.push(key);
      }
    }
    if (MODE_S && !payload.product_asset) {
      throw new Error('????????');
    }
    if (MODE_S && !payload.brand_logo) {
      throw new Error('????? Logo?');
    }
    if (payload.features.length < 3) {
      throw new Error('请填写至少 3 条产品功能点。');
    }
    if (!MODE_S) {
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
    ['[data-role="scenario-positive-prompt"]', '[name="scenario_image"]'],
    scenarioPreview
  );

  bindButton(
    'btn-generate-product',
    'product',
    ['[data-role="product-positive-prompt"]', '[name="product_prompt"]'],
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
    productSecondaryImage,
    productSecondaryWrap,
    featureList,
    title,
    subtitle,
    gallery,
  } = elements;

  const layoutText = buildLayoutPreview(payload);
  const isTemplateB = isTemplateBStage1Data(payload);
  const familyAPreview = document.getElementById('preview-family-a');
  const familyBPreview = document.getElementById('preview-family-b');

  if (layoutStructure) {
    layoutStructure.textContent = layoutText;
  }

  if (previewContainer) {
    previewContainer.classList.remove('hidden');
    previewContainer.dataset.templateFamily = isTemplateB ? 'b' : 'a';
  }
  if (familyAPreview) {
    familyAPreview.classList.toggle('hidden', isTemplateB);
  }
  if (familyBPreview) {
    familyBPreview.classList.toggle('hidden', !isTemplateB);
  }

  if (isTemplateB) {
    const materials = normaliseTemplateBMaterials(payload)
      .map((entry) => resolvePreviewAssetSrc(entry))
      .filter(Boolean);
    const brandLogoEl = document.getElementById('preview-b-brand-logo');
    const brandNameEl = document.getElementById('preview-b-brand-name');
    const agentNameEl = document.getElementById('preview-b-agent-name');
    const skuEl = document.getElementById('preview-b-sku');
    const titleEl = document.getElementById('preview-b-title');
    const subtitleEl = document.getElementById('preview-b-subtitle');
    const productEl = document.getElementById('preview-b-product-image');
    const secondaryWrap = document.getElementById('preview-b-secondary-wrap');
    const secondaryEl = document.getElementById('preview-b-secondary-image');
    const materialsEl = document.getElementById('preview-b-materials');
    const descriptionWrap = document.getElementById('preview-b-description');
    const descriptionTitleEl = document.getElementById('preview-b-description-title');
    const descriptionBodyEl = document.getElementById('preview-b-description-body');

    const primarySrc = resolvePreviewAssetSrc(payload.product_asset || payload.product_image_1) || placeholderImages.product;
    const secondarySrc = resolvePreviewAssetSrc(payload.product_image_2);
    const logoSrc = resolvePreviewAssetSrc(payload.brand_logo) || placeholderImages.brandLogo;
    const descriptionTitle = payload.description_title || '';
    const descriptionBody = payload.description_body || '';

    if (brandLogoEl) brandLogoEl.src = logoSrc;
    if (brandNameEl) brandNameEl.textContent = payload.brand_name || 'Brand';
    if (agentNameEl) {
      agentNameEl.textContent = payload.agent_name || 'Agent';
      agentNameEl.classList.toggle('hidden', !payload.agent_name);
    }
    if (skuEl) {
      skuEl.textContent = payload.sku_text || 'SKU optional';
      skuEl.classList.toggle('hidden', !payload.sku_text);
    }
    if (titleEl) titleEl.textContent = payload.title || 'Title';
    if (subtitleEl) subtitleEl.textContent = payload.subtitle || 'Subtitle';
    if (productEl) productEl.src = primarySrc;
    if (secondaryWrap) secondaryWrap.classList.toggle('hidden', !secondarySrc);
    if (secondaryEl) {
      if (secondarySrc) {
        secondaryEl.src = secondarySrc;
      } else {
        secondaryEl.removeAttribute('src');
      }
    }
    if (materialsEl) {
      materialsEl.innerHTML = '';
      materialsEl.classList.toggle('hidden', materials.length === 0);
      materials.forEach((src, index) => {
        const item = document.createElement('div');
        item.className = 'template-b-preview__material-item';
        const image = document.createElement('img');
        image.src = src;
        image.alt = `Material ${index + 1}`;
        item.appendChild(image);
        materialsEl.appendChild(item);
      });
    }
    if (descriptionWrap) {
      descriptionWrap.classList.toggle('hidden', !(descriptionTitle || descriptionBody));
    }
    if (descriptionTitleEl) {
      descriptionTitleEl.textContent = descriptionTitle || 'Description title';
    }
    if (descriptionBodyEl) {
      descriptionBodyEl.textContent = descriptionBody || 'Description body';
    }
    return layoutText;
  }

  const familyAPreviewRoot = document.getElementById('preview-family-a');
  const logoFallback = resolvePreviewAssetSrc(state.brandLogo) || placeholderImages.brandLogo;
  const limit = state.galleryLimit || 4;
  const entries = buildModeSDefaultGalleryEntries(state.galleryEntries, limit).slice(0, limit);
  const galleryLabel = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;
  const total = Math.max(entries.length, limit);
  const galleryFallbackPlan = buildModeSFamilyAGalleryFallbackPlan({
    productPrimaryRef: state.productImage1,
    productSecondaryRef: state.productImage2,
    logoRef: state.brandLogo,
  });
  const galleryItems = [];
  for (let index = 0; index < total; index += 1) {
    const entry = entries[index];
    const fallbackSources = (galleryFallbackPlan[index] || [state.productImage1, state.productImage2, state.brandLogo])
      .map((asset) => resolvePreviewAssetSrc(asset))
      .filter(Boolean);
    galleryItems.push({
      src: resolvePreviewAssetSrc(entry?.asset) || fallbackSources[0] || logoFallback || '',
      caption: entry?.caption || getModeSDefaultGalleryCaption(index),
    });
  }

  const featuresForPreview = (payload.product_callouts && payload.product_callouts.length)
    ? payload.product_callouts
    : payload.features.length
    ? payload.features
    : DEFAULT_STAGE1.product_callouts || DEFAULT_STAGE1.features;
  const previewModel = buildTemplateAPreviewModel({
    brandName: payload.brand_name || '品牌名称',
    agentName: (payload.agent_name || '代理名 / 分销名').toUpperCase(),
    title: payload.title || '标题文案',
    subtitle: payload.subtitle || '底部辅助文案',
    features: featuresForPreview.slice(0, 3),
    logoSrc: resolvePreviewAssetSrc(payload.brand_logo) || placeholderImages.brandLogo,
    scenarioSrc: resolvePreviewAssetSrc(payload.scenario_asset) || placeholderImages.scenario,
    productPrimarySrc: resolvePreviewAssetSrc(payload.product_asset) || placeholderImages.product,
    productSecondarySrc: resolvePreviewAssetSrc(payload.product_image_2),
    galleryItems,
    latestResult: null,
  });
  applyTemplateAPreviewModel({
    root: familyAPreviewRoot,
    brandLogoEl: brandLogo,
    brandNameEl: brandName,
    agentNameEl: agentName,
    scenarioImageEl: scenarioImage,
    productImageEl: productImage,
    productSecondaryImageEl: productSecondaryImage,
    productSecondaryWrapEl: productSecondaryWrap,
    featureListEl: featureList,
    titleEl: title,
    subtitleEl: subtitle,
    galleryEl: gallery,
    model: previewModel,
    galleryPlaceholderLabel: galleryLabel,
  });

  return layoutText;
}

function buildLayoutPreview(payload) {
  if (MODE_S) {
    if (isTemplateBStage1Data(payload)) {
      const materials = normaliseTemplateBMaterials(payload);
      const lines = [
        'Template B / Family B summary',
        `Template: ${payload.template_id || TEMPLATE_B_ID}`,
        'Region order: logo_banner -> top_copy -> materials_strip -> product_hero -> description',
        `Title: ${payload.title || 'missing'}`,
        `Subtitle: ${payload.subtitle || 'optional'}`,
        `SKU: ${payload.sku_text || 'optional'}`,
        `Brand: ${payload.brand_name || 'n/a'}`,
        `Agent: ${payload.agent_name || 'n/a'}`,
        `Primary product: ${payload.product_image_1 ? 'ready' : 'missing'}`,
        `Supporting detail inset: ${payload.product_image_2 ? 'ready' : 'optional'}`,
        `Materials evidence strip: ${materials.length} item(s)`,
        `Description title: ${payload.description_title || 'optional'}`,
        `Description body: ${payload.description_body ? 'present' : 'optional'}`,
      ];
      return lines.join('\n');
    }

    const callouts = resolveStage1ProductCallouts(payload);
    const lines = [
      'Mode S summary',
      `Channel: ${payload.channel || 'missing'}`,
      `Intent: ${payload.intent || 'missing'}`,
      `Title: ${payload.title || 'missing'}`,
      `Product callouts: ${callouts.length}`,
      `Bottom support copy: ${payload.subtitle || payload.tagline || 'optional'}`,
      `Brand: ${payload.brand_name || 'n/a'}`,
      `Brand color: ${payload.brand_color || 'n/a'}`,
      `Price: ${payload.price || 'n/a'}`,
      `Promo: ${payload.promo || 'n/a'}`,
      `Product image 1: ${payload.product_image_1 ? 'ready' : 'missing'}`,
      `Product image 2: ${payload.product_image_2 ? 'ready' : 'missing'}`,
    ];
    return lines.join('\n');
  }

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

  const featuresPreview = (
    resolveStage1ProductCallouts(payload).length
      ? resolveStage1ProductCallouts(payload)
      : DEFAULT_STAGE1.product_callouts || DEFAULT_STAGE1.features
  )
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
  }\n\n左侧区域（约 40% 宽）\n  · 应用场景图：${scenarioLine}\n\n右侧区域（视觉中心）\n  · 主产品 45° 渲染图：${productLine}\n  · 产品卖点标注：\n${featuresPreview}\n\n中部标题（大号粗体红字）\n  · ${payload.title || '标题文案待补充'}\n\n底部区域（三视图或系列款式）\n${gallerySummary}\n\n角落副标题 / 标语（大号粗体红字）\n  · ${payload.subtitle || '底部辅助文案待补充'}\n\n主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）\n背景：浅灰或白色，保持留白与对齐。`;
}

function serialiseStage1Data(payload, state, layoutPreview, previewBuilt) {
  if (MODE_S) {
    return {
      brand_name: payload.brand_name,
      agent_name: payload.agent_name || '',
      brand_color: payload.brand_color || null,
      price: payload.price || '',
      promo: payload.promo || '',
      channel: payload.channel || null,
      intent: payload.intent || null,
      scenario_image: payload.scenario_image || MODE_S_DEFAULT_STAGE1.scenario_image,
      product_name: payload.product_name || '',
      title: payload.title,
      subtitle: payload.subtitle || payload.tagline || '',
      tagline: payload.tagline || '',
      allow_auto_fill: payload.allow_auto_fill !== false,
      product_callouts: payload.product_callouts || payload.features || payload.bullets || [],
      bullets: payload.bullets || payload.product_callouts || payload.features || [],
      features: payload.features || payload.product_callouts || payload.bullets || [],
      brand_logo: serialiseAssetForStorage(state.brandLogo),
      scenario_asset: serialiseAssetForStorage(state.scenario),
      product_asset: serialiseAssetForStorage(state.productImage1),
      product_image_1: serialiseAssetForStorage(state.productImage1),
      product_image_2: serialiseAssetForStorage(state.productImage2),
        gallery_entries: (state.galleryEntries || [])
          .filter((entry) => entry && entry.asset)
          .map((entry) => ({
            id: entry.id,
            caption: entry.caption || '',
            asset: serialiseAssetForStorage(entry.asset),
            mode: 'upload',
            prompt: null,
          })),
        template_id: state.templateVariant === 'b'
          ? 'template_product_sheet_v1'
          : (state.templateId || DEFAULT_STAGE1.template_id),
        template_variant: state.templateVariant || payload.template_variant || 'a',
      template_label: state.templateLabel || '',
      // Template B fields
      sku_text: state.skuText || null,
      description_title: state.descriptionTitle || null,
      description_body: state.descriptionBody || null,
      materials_images: (state.materialsImages || [])
        .filter((e) => e.url)
        .map((e) => ({ url: e.url, key: e.key || null })),
      layout_preview: layoutPreview,
      preview_built: previewBuilt,
    };
  }

  return {
    brand_name: payload.brand_name,
    agent_name: payload.agent_name,
    scenario_image: payload.scenario_image,
    product_name: payload.product_name,
    channel: payload.channel || null,
    intent: payload.intent || null,
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
    product_asset_extra_1: serialiseAssetForStorage(state.productExtra1),
    product_asset_extra_2: serialiseAssetForStorage(state.productExtra2),
    gallery_entries: (payload.gallery_entries || state.galleryEntries).map((entry) => ({
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
        const key = stage2Meta?.final_poster?.storage_key;
        if (key) {
          void assetStore.delete(key);
        }
      } catch (error) {
        console.warn('清理环节 2 缓存时解析失败。', error);
      }
    }
    sessionStorage.removeItem(STORAGE_KEYS.stage2);
  }

  try {
    const draft = buildDraftFromStage1Data(data);
    saveDraft(draft);
  } catch (error) {
    console.warn('Unable to save draft snapshot', error);
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

function safeParseJson(raw) {
  if (!raw || typeof raw !== 'string') return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function buildDraftFromStage1Data(stage1Data) {
  if (!stage1Data || typeof stage1Data !== 'object') return {};
  const bullets = Array.isArray(stage1Data.bullets) ? stage1Data.bullets : [];
  const productCallouts = resolveStage1ProductCallouts(stage1Data);
  return {
    core: {
      brand_name: stage1Data.brand_name || '',
      brand_color: stage1Data.brand_color || '',
      price: stage1Data.price || '',
      promo: stage1Data.promo || '',
      title: stage1Data.title || '',
      subtitle: resolveTemplateABottomSupportCopy(stage1Data, ''),
      tagline: resolveTemplateABottomSupportCopy(stage1Data, stage1Data.promo || ''),
      bullets: productCallouts.length ? productCallouts : bullets,
      product_callouts: productCallouts,
      product_image_1: stage1Data.product_image_1 || null,
      product_image_2: stage1Data.product_image_2 || null,
    },
    messaging: {
      channel: stage1Data.channel || '',
      intent: stage1Data.intent || '',
    },
    poster: stage1Data,
    prompt_bundle: stage1Data.prompt_bundle || null,
  };
}

function saveDraft(draft) {
  const payload = typeof draft === 'object' && draft ? draft : {};
  const encoded = JSON.stringify(payload);
  localStorage.setItem(DRAFT_STORAGE_KEY, encoded);
  sessionStorage.setItem(DRAFT_STORAGE_KEY, encoded);
}

function loadDraft() {
  const fromLocal = safeParseJson(localStorage.getItem(DRAFT_STORAGE_KEY));
  if (fromLocal && typeof fromLocal === 'object') return fromLocal;
  const fromSession = safeParseJson(sessionStorage.getItem(DRAFT_STORAGE_KEY));
  if (fromSession && typeof fromSession === 'object') return fromSession;
  const stage1Data = loadStage1Data();
  return buildDraftFromStage1Data(stage1Data);
}

function pickDraftImageRef(asset) {
  if (!asset) return null;
  if (typeof asset === 'string') return asset;
  return (
    asset.r2Key ||
    asset.remoteUrl ||
    asset.url ||
    asset.publicUrl ||
    asset.dataUrl ||
    asset.data_url ||
    null
  );
}

function cloneStage2Value(value) {
  if (typeof stage2RequestHelpers.cloneValue === 'function') {
    return stage2RequestHelpers.cloneValue(value);
  }
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(value);
    } catch (error) {
      console.warn('[stage2] structuredClone failed, falling back to JSON clone', error);
    }
  }
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function stage2StableStringify(value) {
  if (typeof stage2RequestHelpers.stableStringify === 'function') {
    return stage2RequestHelpers.stableStringify(value);
  }
  const sortValue = (input) => {
    if (Array.isArray(input)) return input.map(sortValue);
    if (!input || typeof input !== 'object') return input;
    return Object.keys(input)
      .sort()
      .reduce((acc, key) => {
        acc[key] = sortValue(input[key]);
        return acc;
      }, {});
  };
  return JSON.stringify(sortValue(value));
}

function hashStage2StableValue(value) {
  if (typeof stage2RequestHelpers.hashStableValue === 'function') {
    return stage2RequestHelpers.hashStableValue(value);
  }
  const text = typeof value === 'string' ? value : stage2StableStringify(value);
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

function freezeStage2RequestSnapshot(value) {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
  Object.freeze(value);
  Object.values(value).forEach((entry) => {
    freezeStage2RequestSnapshot(entry);
  });
  return value;
}

function buildStage2SourceSignatures(stage1Data) {
  if (typeof stage2RequestHelpers.buildStage2SourceSignatures === 'function') {
    return stage2RequestHelpers.buildStage2SourceSignatures(stage1Data);
  }
  const galleryEntries = Array.isArray(stage1Data?.gallery_entries) ? stage1Data.gallery_entries : [];
  return {
    assetSignature: JSON.stringify({
      brand_logo: pickDraftImageRef(stage1Data?.brand_logo),
      scenario_asset: pickDraftImageRef(stage1Data?.scenario_asset),
      product_image_1: pickDraftImageRef(stage1Data?.product_image_1 || stage1Data?.product_asset),
      product_image_2: pickDraftImageRef(stage1Data?.product_image_2),
      gallery_entries: galleryEntries.map((entry) => ({
        asset: pickDraftImageRef(entry?.asset),
        caption: entry?.caption || '',
      })),
    }),
    copySignature: JSON.stringify({
      title: stage1Data?.title || '',
      subtitle: stage1Data?.subtitle || stage1Data?.tagline || stage1Data?.promo || '',
      features: resolveStage1ProductCallouts(stage1Data),
    }),
  };
}

function buildStage2FormStateSignatures(input = {}) {
  if (typeof stage2RequestHelpers.buildStage2FormStateSignatures === 'function') {
    return stage2RequestHelpers.buildStage2FormStateSignatures(input);
  }
  const source = buildStage2SourceSignatures(input.stage1Data);
  return {
    ...source,
    bottom: cloneStage2Value(input.bottomRequestState || {}),
    copyReviewAcceptance: cloneStage2Value(input.copyOptimization || {}),
    requestControls: cloneStage2Value(input.adjustments || {}),
    bottomSignature: stage2StableStringify(input.bottomRequestState || {}),
    copyReviewAcceptanceSignature: stage2StableStringify(input.copyOptimization || {}),
    requestControlsSignature: stage2StableStringify(input.adjustments || {}),
    formSignature: stage2StableStringify({
      assets: source.assets,
      copy: source.copy,
      bottom: input.bottomRequestState || {},
      copyReviewAcceptance: input.copyOptimization || {},
      requestControls: input.adjustments || {},
    }),
  };
}

function diffStage2FormSignatures(previous, next) {
  if (typeof stage2RequestHelpers.diffStage2FormSignatures === 'function') {
    return stage2RequestHelpers.diffStage2FormSignatures(previous, next);
  }
  if (!previous || !next) return [];
  const changed = [];
  if (previous.assetSignature !== next.assetSignature) changed.push('assets');
  if (previous.copySignature !== next.copySignature) changed.push('copy');
  if (previous.bottomSignature !== next.bottomSignature) changed.push('bottom_contract');
  if (previous.copyReviewAcceptanceSignature !== next.copyReviewAcceptanceSignature) {
    changed.push('copy_optimization_acceptance');
  }
  if (previous.requestControlsSignature !== next.requestControlsSignature) changed.push('request_controls');
  return changed;
}

function buildPoster2PayloadFromNormalisedInputs(input) {
  if (typeof stage2RequestHelpers.buildPoster2PayloadFromNormalisedInputs === 'function') {
    return stage2RequestHelpers.buildPoster2PayloadFromNormalisedInputs(input);
  }
  const galleryImages = Array.isArray(input.galleryImages)
    ? input.galleryImages.map((entry) => ({
        url: entry.url || '',
        key: entry.key || null,
        caption: entry.caption || null,
      }))
    : [];
  const galleryImageCount = galleryImages.length;
  return {
    template_id: input.templateId,
    renderer_mode: input.rendererMode || 'auto',
    brand_name: input.brandName || '',
    agent_name: input.agentName || '',
    title: input.title || '',
    subtitle: input.subtitle || '',
    features: Array.isArray(input.features) ? input.features.slice(0, 4) : [],
    product_image: input.productImage || { url: '', key: null },
    product_secondary_image: input.productSecondaryImage || null,
    logo: input.logo || null,
    scenario_image: input.scenarioImage || null,
    gallery_images: galleryImages,
    gallery_input_count_raw: galleryImageCount,
    gallery_input_count_normalized: galleryImageCount,
    gallery_requested_count: galleryImageCount,
    gallery_autofill_applied: false,
    bottom_mode: input.bottomRequestState?.bottom_mode || 'title_gallery_split',
    gallery_mode: input.bottomRequestState?.gallery_mode || 'strip_local_visible_only',
    style: {
      prompt: input.stylePrompt || '',
    },
    copy_optimization: {
      mode: input.copyOptimization?.mode || 'off',
      decision: input.copyOptimization?.decision || 'pending',
      accepted_title: input.copyOptimization?.accepted_title || input.copyOptimization?.acceptedTitle || '',
      accepted_subtitle: input.copyOptimization?.accepted_subtitle || input.copyOptimization?.acceptedSubtitle || '',
      accepted_features: Array.isArray(input.copyOptimization?.accepted_features)
        ? input.copyOptimization.accepted_features.filter(Boolean).slice(0, 4)
        : Array.isArray(input.copyOptimization?.acceptedFeatures)
        ? input.copyOptimization.acceptedFeatures.filter(Boolean).slice(0, 4)
        : [],
    },
  };
}

function buildGeneratePosterPayloadFromForm(input) {
  if (typeof stage2RequestHelpers.buildGeneratePosterPayloadFromForm === 'function') {
    return stage2RequestHelpers.buildGeneratePosterPayloadFromForm(input);
  }
  return buildPoster2PayloadFromNormalisedInputs(cloneStage2Value(input || {}));
}

function buildPoster2RequestSummary(payload) {
  if (typeof stage2RequestHelpers.buildPoster2RequestSummary === 'function') {
    return stage2RequestHelpers.buildPoster2RequestSummary(payload);
  }
  return {
    template_id: payload?.template_id || null,
    renderer_mode: payload?.renderer_mode || null,
    bottom_mode: payload?.bottom_mode || null,
    gallery_mode: payload?.gallery_mode || null,
    feature_count: Array.isArray(payload?.features) ? payload.features.length : 0,
    gallery_count: Array.isArray(payload?.gallery_images) ? payload.gallery_images.length : 0,
  };
}

function isFamilyACommercialFryerVariantLocal(input) {
  if (typeof stage2RequestHelpers.isFamilyACommercialFryerVariant === 'function') {
    return stage2RequestHelpers.isFamilyACommercialFryerVariant(input);
  }
  const values = [
    input?.titleText,
    input?.subtitleText,
    input?.agentName,
    ...(Array.isArray(input?.featureTexts) ? input.featureTexts : []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return ['fryer', 'fry station', 'stainless steel', 'fast heat', 'fast heating'].some((token) =>
    values.includes(token)
  );
}

function resolveTemplateAPreviewTruthLocal(input) {
  if (typeof stage2RequestHelpers.resolveTemplateAPreviewTruth === 'function') {
    return stage2RequestHelpers.resolveTemplateAPreviewTruth(input);
  }
  return {
    headerMode: 'identity_left_agent_right',
    featureMode: 'product_anchor_callouts',
    annotationOwner: 'product_region',
    bottomMode: input?.bottomMode || 'title_gallery_split',
    galleryMode: input?.galleryMode || 'strip_local_visible_only',
    footerOrdering: 'title_subtitle_above_gallery',
    productComposition: input?.hasSecondaryAsset ? 'single_primary_supporting_inset' : 'single_primary',
    productGeometryMode: input?.hasSecondaryAsset ? 'family_a_fryer_hero_supporting_inset_v1' : 'single_primary_v1',
    fryerVariant: Boolean(input?.hasSecondaryAsset),
    showSecondaryInset: Boolean(input?.hasSecondaryAsset),
    subtitleVisible: Boolean(input?.subtitleText),
    galleryVisible: Number(input?.galleryCount || 0) > 0,
  };
}

function isCurrentStage2Request(requestId) {
  return stage2ActiveRequestId === requestId;
}

function abortActiveStage2Request(reason = 'superseded') {
  if (!stage2ActiveAbortController) return;
  try {
    stage2ActiveAbortController.abort(reason);
  } catch (error) {
    console.warn('[stage2] abort request failed', error);
  }
}

function clearStage2RuntimeRequestCache() {
  const stage2Raw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (stage2Raw) {
    try {
      const stage2Meta = JSON.parse(stage2Raw);
      const key = stage2Meta?.final_poster?.storage_key;
      if (key) {
        void assetStore.delete(key);
      }
    } catch (error) {
      console.warn('[stage2] unable to clear cached stage2 result', error);
    }
  }
  sessionStorage.removeItem(STORAGE_KEYS.stage2);
  lastPosterResult = null;
  lastPromptBundle = null;
  posterGenerationState.promptBundle = null;
  posterGenerationState.rawResult = null;
  stage2State.poster2.latestResult = null;
  stage2State.poster2.history = [];
  stage2State.generated.lastSuccessPosterUrl = null;
  renderPoster2RunHistory();
  updateDebugPanels({ response: null });
}

function clearStage2StoredSuccessReferences() {
  sessionStorage.removeItem(STORAGE_KEYS.stage2);
  if (typeof window !== 'undefined') {
    try {
      const url = new URL(window.location.href);
      if (url.searchParams.has('poster_key')) {
        url.searchParams.delete('poster_key');
        window.history.replaceState({}, '', url.toString());
      }
    } catch (error) {
      console.warn('[stage2] unable to clear poster_key from URL', error);
    }
  }
}

function hasStage2SuccessDerivedState() {
  return Boolean(
    lastPosterResult ||
      lastPromptBundle ||
      posterGenerationState.promptBundle ||
      posterGenerationState.rawResult ||
      posterGeneratedImage ||
      stage2State.poster2.latestResult ||
      stage2State.vertex.lastResponse ||
      stage2State.generated?.lastSuccessPosterUrl ||
      stage2State.generated?.lastCopy ||
      sessionStorage.getItem(STORAGE_KEYS.stage2)
  );
}

function clearStage2DerivedSurfacesBeforeRequest() {
  const hadSuccessState = hasStage2SuccessDerivedState();
  lastPosterResult = null;
  lastPromptBundle = null;
  posterGenerationState.promptBundle = null;
  posterGenerationState.rawResult = null;
  posterGeneratedImage = null;
  stage2State.poster2.latestResult = null;
  stage2State.vertex.lastResponse = null;
  stage2State.generated.lastSuccessPosterUrl = null;
  stage2State.generated.lastCopy = null;
  clearStage2StoredSuccessReferences();
  updateDebugPanels({ payload: null, response: null });
  updatePoster2DiagnosticsPanel(null);
  updateStage2Warnings(null);

  const finalImg = document.getElementById('final-poster-img');
  const finalPlaceholder = document.getElementById('final-poster-placeholder');
  const finalLink = document.getElementById('final-poster-link');
  const finalKey = document.getElementById('final-poster-key');
  const copyButton = document.getElementById('final-poster-copy');
  if (finalImg) {
    finalImg.removeAttribute('src');
    finalImg.classList.add('hidden');
  }
  if (finalPlaceholder) finalPlaceholder.classList.remove('hidden');
  if (finalLink) {
    finalLink.removeAttribute('href');
    finalLink.classList.add('hidden');
  }
  if (finalKey) finalKey.textContent = 'N/A';
  if (copyButton) copyButton.disabled = true;
  return hadSuccessState;
}

function invalidateStage2SuccessDerivedState(reason = 'operator_input_changed', fields = []) {
  if (!hasStage2SuccessDerivedState()) return;
  const clearedSuccessState = clearStage2DerivedSurfacesBeforeRequest();
  refreshPosterLayoutPreview({});
  console.info('[stage2] cleared success-derived state', {
    reason,
    invalidated_fields: fields,
    cleared_success_state: clearedSuccessState,
  });
}

function resetPoster2DerivedCopyOptimization(reason = 'source_changed') {
  const state = ensurePoster2CopyOptimizationState();
  state.decision = 'pending';
  state.acceptedTitle = '';
  state.acceptedSubtitle = '';
  state.acceptedFeatures = [];
  state.latestReview = null;
  renderPoster2CopyOptimizationReview(null);
  console.info('[stage2][poster2] cleared copy optimization state', { reason });
}

function invalidateStage2DerivedStateForSnapshot(stage1Data, options = {}) {
  const buildNext = () => buildStage2FormStateSignatures({
    stage1Data,
    bottomRequestState: options.bottomRequestState || buildPoster2BottomRequestState(stage1Data),
    copyOptimization: options.copyOptimizationState || ensurePoster2CopyOptimizationState(),
    adjustments: options.adjustments || stage2State.adjustments || {},
  });
  let next = buildNext();
  const previous = stage2LastSourceSignatures;
  const assetsChanged = Boolean(previous && previous.assetSignature !== next.assetSignature);
  const copyChanged = Boolean(previous && previous.copySignature !== next.copySignature);
  let invalidatedFields = diffStage2FormSignatures(previous, next);
  const bottomChanged = invalidatedFields.includes('bottom_contract');
  const requestControlsChanged = invalidatedFields.includes('request_controls');
  if (assetsChanged) {
    clearStage2RuntimeRequestCache();
  }
  if (assetsChanged || copyChanged || bottomChanged || requestControlsChanged) {
    resetPoster2DerivedCopyOptimization(
      assetsChanged
        ? 'asset_changed'
        : copyChanged
        ? 'copy_changed'
        : bottomChanged
        ? 'bottom_contract_changed'
        : 'request_controls_changed'
    );
    if (options.copyOptimizationState) {
      const resetState = ensurePoster2CopyOptimizationState();
      options.copyOptimizationState.decision = resetState.decision;
      options.copyOptimizationState.acceptedTitle = resetState.acceptedTitle;
      options.copyOptimizationState.acceptedSubtitle = resetState.acceptedSubtitle;
      options.copyOptimizationState.acceptedFeatures = resetState.acceptedFeatures;
      options.copyOptimizationState.latestReview = resetState.latestReview;
    }
    next = buildNext();
    invalidatedFields = diffStage2FormSignatures(previous, next);
  }
  stage2LastSourceSignatures = next;
  return {
    assetsChanged,
    copyChanged,
    bottomChanged,
    requestControlsChanged,
    invalidatedFields,
    signatures: next,
  };
}

function readStage2OperatorUiValues() {
  const valueOf = (id) => document.getElementById(id)?.value ?? null;
  const checkedOf = (id) => {
    const element = document.getElementById(id);
    return element ? Boolean(element.checked) : null;
  };
  return {
    bottom_title: valueOf('poster2-bottom-title'),
    bottom_subtitle: valueOf('poster2-bottom-subtitle'),
    bottom_mode: valueOf('poster2-bottom-mode'),
    gallery_mode: valueOf('poster2-gallery-mode'),
    detected_gallery_count: document.getElementById('poster2-detected-gallery-count')?.dataset?.galleryCount ?? null,
    copy_optimization_mode: valueOf('poster2-copy-optimization-mode'),
    show_bullets: checkedOf('toggle-bullets'),
    title_size: valueOf('title-size-preset'),
  };
}

function logStage2RequestBoundary({
  requestId,
  currentUiValues,
  canonicalFormState,
  requestSnapshot,
  previousResponsePresence,
  invalidatedFields,
  preflightDiagnostics,
}) {
  console.info('[stage2] request boundary', {
    request_id: requestId,
    current_ui_values: currentUiValues,
    canonical_form_state: canonicalFormState,
    request_snapshot: requestSnapshot,
    previous_response_presence: previousResponsePresence,
    invalidated_fields: invalidatedFields,
    preflight_diagnostics: preflightDiagnostics || null,
  });
}

function buildStage2PreflightDiagnostics(input) {
  if (typeof stage2RequestHelpers.buildStage2PreflightDiagnostics === 'function') {
    return stage2RequestHelpers.buildStage2PreflightDiagnostics(input);
  }
  return {
    request_id: input?.requestId ?? null,
    current_bottom_mode: input?.formSignatures?.bottom?.bottom_mode || null,
    previous_success_present: Boolean(input?.previousSuccessPresent),
    invalidated_fields: Array.isArray(input?.invalidatedFields) ? input.invalidatedFields : [],
    cleared_success_state: Boolean(input?.clearedSuccessState),
    detected_gallery_items: Number(input?.detectedGalleryItems || 0),
    canonical_form_signature_hash: hashStage2StableValue(input?.formSignatures?.formSignature || ''),
    request_payload_signature_hash: hashStage2StableValue(input?.payload || {}),
  };
}

function syncStage2PreviewStateFromStage1(snapshot) {
  if (!snapshot || typeof snapshot !== 'object') return;
  const stage1Features = Array.isArray(snapshot.features)
    ? snapshot.features.filter(Boolean)
    : [];
  const stage1Bullets = Array.isArray(snapshot.bullets)
    ? snapshot.bullets.filter(Boolean)
    : [];
  const stage2Features = stage1Features.length ? stage1Features : stage1Bullets;
  stage2State.poster = {
    brand_name: snapshot.brand_name || '',
    agent_name: snapshot.agent_name || '',
    headline: snapshot.title || '',
    subtitle: resolveTemplateABottomSupportCopy(snapshot, ''),
    tagline: resolveTemplateABottomSupportCopy(snapshot, ''),
    features: stage2Features,
    series: Array.isArray(snapshot.gallery_entries)
      ? snapshot.gallery_entries.filter(Boolean).map((entry) => ({ name: entry.caption || '' }))
      : [],
    gallery_entries: Array.isArray(snapshot.gallery_entries)
      ? snapshot.gallery_entries.filter(Boolean)
      : [],
  };
  stage2State.assets = {
    brand_logo_url: pickImageSrc(snapshot.brand_logo) || '',
    scenario_url: pickImageSrc(snapshot.scenario_asset) || '',
    product_url: pickImageSrc(snapshot.product_asset || snapshot.product_image_1) || '',
    gallery_urls: Array.isArray(snapshot.gallery_entries)
      ? snapshot.gallery_entries
          .map((entry) => pickImageSrc(entry?.asset))
          .filter(Boolean)
      : [],
    composite_poster_url: '',
  };
}

function getKitPosterVariant(renderMode) {
  if (renderMode === 'kitposter1_b') return 'b';
  return 'a';
}

function buildKitPosterDraftFromSource(source, adjustments, renderMode) {
  const payload = source && typeof source === 'object' ? source : {};
  const bullets = resolveStage1ProductCallouts(payload);
  const productImages = [];
  const image1 = pickDraftImageRef(payload.product_image_1 || payload.productImage1);
  const image2 = pickDraftImageRef(payload.product_image_2 || payload.productImage2);
  if (image1) productImages.push(image1);
  if (image2) productImages.push(image2);

  const showBullets = adjustments?.showBullets !== false;
  return {
    template_id: payload.template_id || DEFAULT_STAGE1.template_id,
    variant: getKitPosterVariant(renderMode),
    product_images: productImages,
    copy: {
      title: payload.title || '',
      bullets: showBullets ? bullets : [],
      tagline: payload.subtitle || payload.tagline || payload.promo || null,
    },
    options: {
      quality_mode: adjustments?.qualityMode || 'stable',
    },
  };
}

function buildGeneratePosterPayload(draft) {
  const core = draft?.core || {};
  const messaging = draft?.messaging || {};
  const posterSource = draft?.poster || {};
  const stage1Snapshot = loadStage1Data();
  const draftSource = stage1Snapshot || core || posterSource;
  if (isTemplateBStage1Data(draftSource)) {
    return {
      template_id: TEMPLATE_B_ID,
      renderer_mode: 'auto',
      brand_name: draftSource.brand_name || '',
      agent_name: draftSource.agent_name || '',
      title: draftSource.title || '',
      subtitle: draftSource.subtitle || '',
      sku_text: draftSource.sku_text || '',
      description_title: draftSource.description_title || draftSource.descriptionTitle || '',
      description_body: draftSource.description_body || draftSource.descriptionBody || '',
      product_image_1: pickDraftImageRef(draftSource.product_image_1),
      product_image_2: pickDraftImageRef(draftSource.product_image_2),
      materials_images: normaliseTemplateBMaterials(draftSource).map((entry) => ({
        url: entry.url || entry.dataUrl || null,
        key: entry.key || null,
      })),
      features: [],
      gallery_images: [],
    };
  }

  const bullets = normaliseStage1ProductCallouts(core.product_callouts || core.bullets);
  const title = core.title || posterSource.title || '';
  const showBullets = stage2State.adjustments?.showBullets !== false;
  const renderMode = stage2State.renderMode || 'kitposter1_a';
  const draftPayload = buildKitPosterDraftFromSource(
    draftSource,
    stage2State.adjustments,
    renderMode
  );
  const featureBullets = showBullets ? bullets : [];
  return {
    poster: {
      brand_name: core.brand_name || posterSource.brand_name || '',
      agent_name: resolveModeSAgentName(
        posterSource.agent_name || messaging.channel || '',
        core.brand_name || posterSource.brand_name || ''
      ),
      scenario_image: posterSource.scenario_image || messaging.intent || '',
      product_name: posterSource.product_name || title || '',
      channel: messaging.channel || posterSource.channel || null,
      intent: messaging.intent || posterSource.intent || null,
      template_id: posterSource.template_id || DEFAULT_STAGE1.template_id,
      features: featureBullets,
      title,
      subtitle: posterSource.subtitle || core.subtitle || posterSource.tagline || core.tagline || '',
      series_description: posterSource.series_description || '',
      brand_color: core.brand_color || posterSource.brand_color || null,
      price: core.price || posterSource.price || null,
      promo: core.promo || posterSource.promo || null,
      product_image_1: pickDraftImageRef(core.product_image_1),
      product_image_2: pickDraftImageRef(core.product_image_2),
    },
    draft: draftPayload,
    render_mode: renderMode,
    variants: 1,
    seed: 0,
    lock_seed: true,
    prompt_bundle: draft?.prompt_bundle || null,
  };
}

async function buildPoster2GeneratePayload(stage1Data, apiCandidates, options = {}) {
  const copyOptimizationState = cloneStage2Value(options.copyOptimizationState || ensurePoster2CopyOptimizationState());
  const bottomRequestState = cloneStage2Value(
    options.bottomRequestState || buildPoster2BottomRequestState(stage1Data)
  );
  const adjustments = cloneStage2Value(options.adjustments || stage2State.adjustments || {});
  const rendererMode = options.rendererMode || stage2State.poster2.rendererMode || 'auto';
  const safeText = (value, fallback = '') => {
    const text = typeof value === 'string' ? value.trim() : '';
    return text || fallback;
  };
  const pickPoster2StylePrompt = () => {
    const candidates = [
      stage1Data.scenario_prompt,
      stage1Data.intent,
      stage1Data.tagline,
      stage1Data.subtitle,
      stage1Data.title,
    ];
    for (const candidate of candidates) {
      const text = safeText(candidate, '');
      if (!text) continue;
      if (/^(https?:|data:|r2:)/i.test(text)) continue;
      if (text.toLowerCase() === 'default') continue;
      return text;
    }
    return 'clean studio background, soft diffused light';
  };

  const brandName = safeText(stage1Data.brand_name, MODE_S_DEFAULT_STAGE1.brand_name || 'Brand');
  const title = bottomRequestState.sanitized_title_text;
  const agentName = resolveModeSAgentName(
    stage1Data.agent_name || MODE_S_DEFAULT_STAGE1.agent_name || stage1Data.channel || '',
    brandName
  );
  const subtitle = bottomRequestState.sanitized_subtitle_text;
  const requestedGalleryCount = bottomRequestState.requested_gallery_count;
  const featureSource = Array.isArray(stage1Data.product_callouts) && stage1Data.product_callouts.length
    ? stage1Data.product_callouts
    : Array.isArray(stage1Data.features) && stage1Data.features.length
    ? stage1Data.features
    : Array.isArray(stage1Data.bullets)
    ? stage1Data.bullets
    : [];
  const features = (adjustments?.showBullets !== false
    ? featureSource
    : []
  )
    .filter(Boolean)
    .slice(0, 4);

  const productRef = await normaliseAssetReference(
    stage1Data.product_image_1 || stage1Data.product_asset,
    {
      field: 'poster2.product_image',
      required: true,
      apiCandidates,
      folder: 'product',
    },
    null
  );

  const productSecondaryRef = await normaliseAssetReference(
    stage1Data.product_image_2,
    {
      field: 'poster2.product_secondary_image',
      required: false,
      apiCandidates,
      folder: 'product',
    },
    null
  );

  const logoRef = await normaliseAssetReference(
    stage1Data.brand_logo,
    {
      field: 'poster2.logo',
      required: false,
      apiCandidates,
      folder: 'logo',
    },
    null
  );

  const scenarioRef = await normaliseAssetReference(
    stage1Data.scenario_asset,
    {
      field: 'poster2.scenario_image',
      required: false,
      apiCandidates,
      folder: 'scenario',
    },
    null
  );

  const galleryRefs = [];
  const galleryEntries = (Array.isArray(stage1Data.gallery_entries) ? stage1Data.gallery_entries : [])
    .filter((entry) => entry?.asset)
    .slice(0, requestedGalleryCount);
  for (let index = 0; index < galleryEntries.length; index += 1) {
    const entry = galleryEntries[index];
    if (entry?.asset) {
      // eslint-disable-next-line no-await-in-loop
      const ref = await normaliseAssetReference(
        entry.asset,
        {
          field: 'poster2.gallery_images',
          required: false,
          apiCandidates,
          folder: 'gallery',
        },
        null
      );
      if (ref?.url) {
        galleryRefs.push({
          url: ref.url,
          key: ref.key || null,
          caption: entry.caption || getModeSDefaultGalleryCaption(index),
          source_role: 'gallery_entry',
        });
        continue;
      }
    }
  }

  const payload = buildGeneratePosterPayloadFromForm({
    templateId: POSTER2_PILOT_TEMPLATE_ID,
    rendererMode,
    brandName,
    agentName,
    title,
    subtitle,
    features,
    productImage: {
      url: productRef?.url || '',
      key: productRef?.key || null,
    },
    productSecondaryImage: productSecondaryRef?.url
      ? {
          url: productSecondaryRef.url,
          key: productSecondaryRef.key || null,
        }
      : null,
    logo: logoRef?.url
      ? {
          url: logoRef.url,
          key: logoRef.key || null,
        }
      : null,
    scenarioImage: scenarioRef?.url
      ? {
          url: scenarioRef.url,
          key: scenarioRef.key || null,
        }
      : null,
    galleryImages: galleryRefs.map((ref) => ({
      url: ref.url,
      key: ref.key || null,
      caption: ref.caption || null,
    })),
    bottomRequestState,
    stylePrompt: pickPoster2StylePrompt(),
    copyOptimization: {
      mode: copyOptimizationState.mode || 'off',
      decision: copyOptimizationState.decision || 'pending',
      acceptedTitle: copyOptimizationState.acceptedTitle || '',
      acceptedSubtitle: copyOptimizationState.acceptedSubtitle || '',
      acceptedFeatures: Array.isArray(copyOptimizationState.acceptedFeatures)
        ? copyOptimizationState.acceptedFeatures.filter(Boolean).slice(0, 4)
        : [],
    },
  });

  return {
    payload,
    refs: {
      productRef,
      productSecondaryRef,
      logoRef,
      scenarioRef,
      galleryRefs,
    },
  };
}

async function buildTemplateBPosterPayload(stage1Data, apiCandidates, options = {}) {
  const safeText = (value, fallback = '') => {
    const text = typeof value === 'string' ? value.trim() : '';
    return text || fallback;
  };

  const brandName = safeText(stage1Data.brand_name, 'Brand');
  const agentName = sanitizeAgentName(stage1Data.agent_name || '', brandName);
  const title = safeText(stage1Data.title, 'Product Sheet');
  const subtitle = safeText(stage1Data.subtitle, '');
  const skuText = safeText(stage1Data.sku_text, '');
  const descriptionTitle = safeText(
    stage1Data.description_title || stage1Data.descriptionTitle,
    ''
  );
  const descriptionBody = safeText(
    stage1Data.description_body || stage1Data.descriptionBody,
    ''
  );

  const productRef = await normaliseAssetReference(
    stage1Data.product_image_1 || stage1Data.product_asset,
    {
      field: 'poster2.template_b.product_image',
      required: true,
      apiCandidates,
      folder: 'product',
    },
    null
  );
  const productSecondaryRef = await normaliseAssetReference(
    stage1Data.product_image_2,
    {
      field: 'poster2.template_b.product_secondary_image',
      required: false,
      apiCandidates,
      folder: 'product',
    },
    null
  );
  const logoRef = await normaliseAssetReference(
    stage1Data.brand_logo,
    {
      field: 'poster2.template_b.logo',
      required: false,
      apiCandidates,
      folder: 'logo',
    },
    null
  );

  const materials = [];
  for (const entry of normaliseTemplateBMaterials(stage1Data).slice(0, 5)) {
    // eslint-disable-next-line no-await-in-loop
    const ref = await normaliseAssetReference(
      entry,
      {
        field: 'poster2.template_b.materials_images',
        required: false,
        apiCandidates,
        folder: 'materials',
      },
      null
    );
    if (ref?.url) {
      materials.push({
        url: ref.url,
        key: ref.key || null,
      });
    }
  }

  const rendererMode = options.rendererMode || stage2State.poster2.rendererMode || 'auto';
  const payload = {
    template_id: TEMPLATE_B_ID,
    renderer_mode: rendererMode,
    brand_name: brandName,
    agent_name: agentName,
    title,
    subtitle,
    features: [],
    product_image: {
      url: productRef?.url || '',
      key: productRef?.key || null,
    },
    product_secondary_image: productSecondaryRef?.url
      ? {
          url: productSecondaryRef.url,
          key: productSecondaryRef.key || null,
        }
      : null,
    logo: logoRef?.url
      ? {
          url: logoRef.url,
          key: logoRef.key || null,
        }
      : null,
    scenario_image: null,
    gallery_images: [],
    materials_images: materials,
    description_title: descriptionTitle,
    description_body: descriptionBody,
    sku_text: skuText,
    style: {
      prompt: safeText(stage1Data.title || stage1Data.description_title, 'clean studio background, soft diffused light'),
    },
  };

  return {
    payload,
    refs: {
      logoRef,
      productRef,
      productSecondaryRef,
      materials,
    },
  };
}

function renderDraftSnapshot(draft) {
  const core = draft?.core || {};
  const messaging = draft?.messaging || {};
  const bullets = Array.isArray(core.bullets) ? core.bullets : [];
  setText('draft-brand-name', core.brand_name || 'N/A');
  setText('draft-brand-color', core.brand_color || 'N/A');
  setText('draft-price', core.price || 'N/A');
  setText('draft-promo', core.promo || 'N/A');
  setText('draft-channel', messaging.channel || 'N/A');
  setText('draft-intent', messaging.intent || 'N/A');
  setText('draft-title', core.title || 'N/A');
  setText('draft-image-1', pickDraftImageRef(core.product_image_1) || 'N/A');
  setText('draft-image-2', pickDraftImageRef(core.product_image_2) || 'N/A');

  const bulletsList = document.getElementById('draft-bullets');
  if (bulletsList) {
    bulletsList.innerHTML = '';
    bullets.forEach((item) => {
      const li = document.createElement('li');
      li.textContent = item;
      bulletsList.appendChild(li);
    });
  }

  const draftKeys = draft && typeof draft === 'object' ? Object.keys(draft) : [];
  setText('stage2-draft-status', `Draft loaded: ${draftKeys.length ? 'yes' : 'no'}`);
  setText('stage2-draft-keys', draftKeys.length ? `Draft keys: ${draftKeys.join(', ')}` : 'Draft keys: none');
}

let promptPresetsDebugLogged = false;

function isStage2Page() {
  const path = (location?.pathname || '').toLowerCase();
  if (path.endsWith('/stage2.html')) return true;
  return Boolean(document?.querySelector?.('[data-preset-select]'));
}

function getPromptInspectorRoot() {
  return document.getElementById('prompt-inspector');
}

function normalizePromptPresetsPayload(raw) {
  const root = raw?.presets || {};
  const hasBuckets = root?.scenario && root?.product && root?.gallery;
  const presetsBySlot = hasBuckets
    ? root
    : {
        scenario: root || {},
        product: root || {},
        gallery: root || {},
      };
  const defaultAssignments = raw?.defaultAssignments || {};
  return { presetsBySlot, defaultAssignments };
}

function getSlotPresets(presets, slot) {
  const normalised = normalizePromptPresetsPayload(presets || {});
  return normalised.presetsBySlot?.[slot] || {};
}

function readModeSPresetAssignmentsFromDOM() {
  const root = getPromptInspectorRoot();
  if (!root) return null;

  const out = {};
  root.querySelectorAll('[data-preset-select]').forEach((el) => {
    const k = el.getAttribute('data-preset-select');
    out[k] = (el.value || '').trim();
  });

  return Object.values(out).some(Boolean) ? out : null;
}

function populatePromptPresetDropdowns(presets) {
  const root = getPromptInspectorRoot();
  if (!root) return;
  root.querySelectorAll('[data-preset-select]').forEach((el) => {
    const k = el.getAttribute('data-preset-select');
    populatePresetSelect(el, presets, k);
  });
}

async function hydrateModeSPresetDropdowns() {
  const root = getPromptInspectorRoot();
  if (!root) return;

  const presets = await loadPromptPresets();
  const normalised = normalizePromptPresetsPayload(presets || {});
  if (!promptPresetsDebugLogged) {
    promptPresetsDebugLogged = true;
    console.log('[stage2] presets slots', Object.keys(normalised.presetsBySlot || {}), {
      scenario: Object.keys(normalised.presetsBySlot?.scenario || {}).length,
      product: Object.keys(normalised.presetsBySlot?.product || {}).length,
      gallery: Object.keys(normalised.presetsBySlot?.gallery || {}).length,
    }, normalised.defaultAssignments || {});
  }
  populatePromptPresetDropdowns(presets);

  const assigns = presets?.defaultAssignments || {};
  root.querySelectorAll('[data-preset-select]').forEach((el) => {
    const k = el.getAttribute('data-preset-select');
    if (!el.value && assigns[k]) el.value = assigns[k];
  });
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

async function buildModeSPromptBundle(stage1Data) {
  try {
    const presets = await loadPromptPresets();
    const uiAssigns = readModeSPresetAssignmentsFromDOM();
    const assignments = uiAssigns || presets.defaultAssignments || {};

    const scenarioPresetId = assignments.scenario || presets.defaultAssignments?.scenario;
    const productPresetId = assignments.product || presets.defaultAssignments?.product;
    const galleryPresetId = assignments.gallery || presets.defaultAssignments?.gallery;

    const scenarioPreset = presets.presets?.scenario?.[scenarioPresetId] || null;
    const productPreset = presets.presets?.product?.[productPresetId] || null;
    const galleryPreset = presets.presets?.gallery?.[galleryPresetId] || null;

    return {
      scenario: scenarioPreset
        ? { preset: scenarioPresetId, positive: scenarioPreset.positive, negative: scenarioPreset.negative, aspect: scenarioPreset.aspect }
        : null,
      product: productPreset
        ? { preset: productPresetId, positive: productPreset.positive, negative: productPreset.negative, aspect: productPreset.aspect }
        : null,
      gallery: galleryPreset
        ? { preset: galleryPresetId, positive: galleryPreset.positive, negative: galleryPreset.negative, aspect: galleryPreset.aspect }
        : null,
    };
  } catch (error) {
    console.warn('[ModeS] prompt presets unavailable', error);
    return { scenario: null, product: null, gallery: null };
  }
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

function normalizeMaybeText(v) {
  if (v === null || v === undefined) return undefined;
  if (typeof v === 'string') {
    const t = v.trim();
    return t.length ? v : undefined;
  }
  return v;
}

function nonEmptyStr(v) {
  return normalizeMaybeText(v);
}

function createPromptState(stage1Data, presets) {
  const state = {
    slots: {},
    seed: parseSeed(stage1Data?.prompt_seed),
    lockSeed: Boolean(stage1Data?.prompt_lock_seed),
    variants: clampVariants(Number(stage1Data?.prompt_variants) || DEFAULT_PROMPT_VARIANTS),
  };
  const savedSlots = stage1Data?.prompt_settings || {};
  const defaults = presets.defaultAssignments || {};
  PROMPT_SLOTS.forEach((slot) => {
    const presetMap = getSlotPresets(presets, slot);
    const saved = savedSlots?.[slot] || {};
    const fallbackId = defaults?.[slot] || Object.keys(presetMap)[0] || null;
    const presetId = normalizeMaybeText(saved.preset) || fallbackId;
    const preset = (presetMap && presetId ? presetMap[presetId] : null) || {};
    const positive = normalizeMaybeText(saved.positive) ?? preset?.positive ?? '';
    const negative = normalizeMaybeText(saved.negative) ?? preset?.negative ?? '';
    const aspect = normalizeMaybeText(saved.aspect) ?? preset?.aspect ?? '';
    state.slots[slot] = {
      preset: presetId,
      positive,
      negative,
      aspect,
    };
  });
  return state;
}

function isPromptSettingsEmpty(stage1Data) {
  const savedSlots = stage1Data?.prompt_settings;
  if (!savedSlots || typeof savedSlots !== 'object') return true;
  return !PROMPT_SLOTS.some((slot) => {
    const entry = savedSlots?.[slot];
    if (!entry || typeof entry !== 'object') return false;
    return Boolean(entry.preset || entry.positive || entry.negative || entry.aspect);
  });
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
    const pos = nonEmptyStr(entry.positive);
    const neg = nonEmptyStr(entry.negative);
    const asp = nonEmptyStr(entry.aspect);
    payload[slot] = {
      preset: entry.preset || null,
      ...(pos !== undefined ? { positive: pos } : {}),
      ...(neg !== undefined ? { negative: neg } : {}),
      ...(asp !== undefined ? { aspect: asp } : {}),
    };
  });
  return payload;
}

function isPromptBundleEmpty(bundle) {
  if (!bundle || typeof bundle !== 'object') return true;
  return !PROMPT_SLOTS.some((slot) => {
    const entry = bundle[slot];
    if (!entry) return false;
    if (typeof entry === 'string') return entry.trim().length > 0;
    if (typeof entry === 'object') {
      return Boolean(entry.preset || entry.positive || entry.negative || entry.aspect);
    }
    return false;
  });
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
  const defaults = presets?.defaultAssignments || {};

  const promptSections = [];
  PROMPT_SLOTS.forEach((slot) => {
    const slotSpec = slotMap[slot];
    if (!slotSpec) return;
    const label = PROMPT_SLOT_LABELS_EN[slot] || slot;
    const guidance = slotSpec.guidance || {};
    const presetId = guidance.preset || defaults[slot] || null;
    const slotPresets = getSlotPresets(presets, slot);
    const preset = presetId ? slotPresets[presetId] || null : null;
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
      const presetMap = getSlotPresets(presets, slot);
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

function updatePromptSummaryLines(state, presets) {
  if (!state?.slots) return;
  PROMPT_SLOTS.forEach((slot) => {
    const summaryEl = document.querySelector(`[data-preset-summary="${slot}"]`);
    if (!summaryEl) return;
    const entry = state.slots?.[slot] || {};
    const presetMap = getSlotPresets(presets, slot);
    const presetLabel = entry.preset ? (presetMap[entry.preset]?.label || entry.preset) : '';
    const hasCustom = Boolean((entry.positive || '').trim() || (entry.negative || '').trim());
    let summary = 'No preset';
    if (presetLabel) {
      summary = hasCustom ? `${presetLabel} (custom)` : presetLabel;
    } else if (hasCustom) {
      summary = 'Custom';
    }
    summaryEl.textContent = summary;
  });
}

function populatePresetSelect(select, presets, slot) {
  if (!select) return;
  select.innerHTML = '';
  const presetMap = getSlotPresets(presets, slot);
  const entries = Object.entries(presetMap);
  if (!entries.length) {
    select.disabled = true;
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No presets loaded';
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
  const container = document.querySelector('#prompt-inspector');
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

  // Stage2: Advanced (Prompt Editing) fields may live outside #prompt-inspector.
  // Bind by container first, then fall back to document-level selector.
  const q = (sel) => container.querySelector(sel) || document.querySelector(sel);

  const selects = {};
  const positives = {};
  const negatives = {};
  const aspects = {};
  const resets = {};

  PROMPT_SLOTS.forEach((slot) => {
    selects[slot] = container.querySelector(`[data-preset-select="${slot}"]`);
    positives[slot] = q(`[data-positive="${slot}"]`);
    negatives[slot] = q(`[data-negative="${slot}"]`);
    aspects[slot] = q(`[data-aspect="${slot}"]`);
    resets[slot] = q(`[data-reset="${slot}"]`);
    populatePresetSelect(selects[slot], presets, slot);
  });

  console.log('[stage2] inspector elements found', {
    selects: Object.fromEntries(PROMPT_SLOTS.map(s => [s, !!selects[s]])),
    positives: Object.fromEntries(PROMPT_SLOTS.map(s => [s, !!positives[s]])),
    negatives: Object.fromEntries(PROMPT_SLOTS.map(s => [s, !!negatives[s]])),
    aspects: Object.fromEntries(PROMPT_SLOTS.map(s => [s, !!aspects[s]])),
  });

  const seedInput = q('#prompt-seed');
  const lockSeedCheckbox = q('#prompt-lock-seed');
  const variantsInput = q('#prompt-variants');
  const previewButton = q('#preview-prompts');
  const abButton = q('#generate-ab');

  const elements = {
    selects,
    positives,
    negatives,
    aspects,
    seedInput,
    lockSeedCheckbox,
    variantsInput,
  };

  const shouldHydrateDefaults = isPromptSettingsEmpty(stage1Data);
  const state = createPromptState(stage1Data, presets);
  applyPromptStateToInspector(state, elements, presets);
  console.log('[stage2] hydrated prompt slot sample', {
    scenario: state?.slots?.scenario,
    product: state?.slots?.product,
    gallery: state?.slots?.gallery,
  });
  if (shouldHydrateDefaults) {
    persistPromptState(stage1Data, state);
  }
  updatePromptSummaryLines(state, presets);

  const emitStateChange = () => {
    updatePromptSummaryLines(state, presets);
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
    const preset = getSlotPresets(presets, slot)?.[presetId] || {};
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
    const posterTemplateImage = document.getElementById('poster-template-image');
    const posterTemplatePlaceholder = document.getElementById('poster-template-placeholder');
    const posterTemplateLink = document.getElementById('poster-template-link');
    const posterPreviewSection = document.getElementById('stage2-poster-preview-section');
    const promptGroup = document.querySelector('#prompt-group');
    const promptDefaultGroup = document.querySelector('#prompt-default-group');
    const promptBundleGroup = document.querySelector('#prompt-bundle-group');
    const emailGroup = document.getElementById('email-group');
    const promptTextarea = document.querySelector('#openai-request-prompt');
    const defaultPromptTextarea = document.querySelector('#template-default-prompt');
    const promptBundlePre = document.querySelector('#prompt-bundle-json');
    const emailTextarea = document.getElementById('generated-email');
    const generateButton = document.getElementById('generate-poster');
    const regenerateButton = document.getElementById('regenerate-poster');
    const promptInspector = document.querySelector('#prompt-inspector');
    const nextButton = document.getElementById('to-stage3');
    const overviewList = document.getElementById('stage1-overview');
    const templateSelect = document.getElementById('template-select');
    const templateCanvas = document.getElementById('template-preview-canvas');
    const templateDescription = document.getElementById('template-description');
    const apiBaseInput = document.getElementById('api-base');
    const posterLayout = document.getElementById('posterB-layout');
    const exportPosterButton = document.getElementById('export-poster-b');
    const stage2Wireframe = document.getElementById('stage2-wireframe');
    const stage2WireframeWarning = document.getElementById('stage2-wireframe-warning');
    const toggleBulletsInput = document.getElementById('toggle-bullets');
    const titleSizePreset = document.getElementById('title-size-preset');
    const fallbackStableButton = document.getElementById('fallback-stable');
    const assetFallbackWarning = document.getElementById('asset-fallback-warning');
    let warningElement = document.getElementById('stage2-warning');

    if (!generateButton || !nextButton) {
      return;
    }

    const draft = loadDraft();
    stage2State.draft = draft;
    renderDraftSnapshot(draft);
    const hasDebugPanels = document.getElementById('debug-draft') || document.getElementById('debug-payload');
    if (hasDebugPanels) {
      updateDebugPanels({ draft });
      bindCopyButton('debug-copy-draft', () => JSON.stringify(stage2State.debugDraft || {}, null, 2));
      bindCopyButton('debug-copy-payload', () => JSON.stringify(stage2State.debugPayload || {}, null, 2));
      bindCopyButton('debug-copy-response', () => JSON.stringify(stage2State.debugResponse || {}, null, 2));
      bindCopyButton('debug-copy-prompt', () => (document.getElementById('debug-prompt-preview')?.value || ''));
    }

      if (posterPreviewSection) {
        posterPreviewSection.classList.remove('hidden');
      }
    if (regenerateButton) {
      regenerateButton.classList.add('hidden');
      regenerateButton.disabled = true;
    }

    const stage1Data = loadStage1Data();
    const refreshStage2Wireframe = () => {
      if (!stage1Data || !stage2Wireframe) return;
      updateWireframePreview(
        stage2Wireframe,
        {
          title: stage1Data.title || '',
          bullets: stage1Data.bullets || [],
          tagline: stage1Data.tagline || stage1Data.promo || '',
        },
        stage1Data.template_id || DEFAULT_STAGE1.template_id,
        stage2WireframeWarning,
        {
          titleScale: stage2State.adjustments.titleScale,
          showBullets: stage2State.adjustments.showBullets,
        }
      );
    };

    if (toggleBulletsInput) {
      toggleBulletsInput.checked = stage2State.adjustments.showBullets !== false;
      toggleBulletsInput.addEventListener('change', () => {
        stage2State.adjustments.showBullets = toggleBulletsInput.checked;
        invalidateStage2SuccessDerivedState('request_controls_changed', ['request_controls']);
        refreshStage2Wireframe();
        renderPosterResult();
        updateDebugPanels({ payload: buildGeneratePosterPayload(stage2State.draft) });
      });
    }

      if (titleSizePreset) {
        titleSizePreset.value = 'M';
        stage2State.adjustments.titleScale = TITLE_SCALE_PRESETS[titleSizePreset.value] || 1;
        stage2State.adjustments.titleSize = titleSizePreset.value;
        titleSizePreset.addEventListener('change', () => {
          const next = TITLE_SCALE_PRESETS[titleSizePreset.value] || 1;
          stage2State.adjustments.titleScale = next;
          stage2State.adjustments.titleSize = titleSizePreset.value;
          invalidateStage2SuccessDerivedState('request_controls_changed', ['request_controls']);
          refreshStage2Wireframe();
          updateDebugPanels({ payload: buildGeneratePosterPayload(stage2State.draft) });
        });
      }

      if (fallbackStableButton) {
        fallbackStableButton.addEventListener('click', () => {
          stage2State.adjustments = {
            showBullets: true,
            titleScale: 1,
            qualityMode: 'stable',
            titleSize: 'M',
            fallbackStableClicked: true,
          };
          if (toggleBulletsInput) toggleBulletsInput.checked = true;
          if (titleSizePreset) titleSizePreset.value = 'M';
        invalidateStage2SuccessDerivedState('request_controls_changed', ['request_controls']);
        refreshStage2Wireframe();
        updateDebugPanels({ payload: buildGeneratePosterPayload(stage2State.draft) });
        setStatus(statusElement, '已请求使用稳定模式。', 'info');
        void runStage2Generation({ isRegenerate: true });
      });
    }
    const previewPayload = buildGeneratePosterPayload(draft);
    updateDebugPanels({ payload: previewPayload });
    if (MODE_S && (!previewPayload.prompt_bundle || !Object.keys(previewPayload.prompt_bundle || {}).length)) {
      try {
        const bundle = await buildModeSPromptBundle(stage1Data);
        previewPayload.prompt_bundle = bundle;
        updateDebugPanels({ payload: previewPayload });
      } catch (error) {
        console.warn('[debug] unable to build prompt bundle preview', error);
      }
    }
    if (!stage1Data || !stage1Data.preview_built) {
      setStatus(statusElement, '请先完成环节 1 的素材输入与版式预览。', 'warning');
      generateButton.disabled = true;
      if (regenerateButton) {
        regenerateButton.disabled = true;
      }
      return;
    }

    initStage2Poster2PilotControls(stage1Data, statusElement);
    initPoster2BottomContractControls(stage1Data, statusElement);
    initPoster2CopyOptimizationControls(stage1Data, statusElement);
    applyStage2TemplateFamilyVisibility(stage1Data);

    refreshStage2Wireframe();

    const variantMode =
      stage1Data?.template_variant === 'b' ? 'kitposter1_b' : 'kitposter1_a';
    stage2State.renderMode = MODE_S ? variantMode : stage2State.renderMode;
    if (!MODE_S && !warningElement && statusElement?.parentNode) {
      warningElement = document.createElement('p');
      warningElement.id = 'stage2-warning';
      warningElement.className = 'hint hidden';
      statusElement.parentNode.insertBefore(warningElement, statusElement.nextSibling);
    }

    if (!MODE_S) {
      initStage2RenderModeControl(promptInspector, statusElement);
    }
    ensureStage2FinalPosterPreview(posterOutput);

    await hydrateStage1DataAssets(stage1Data);
  if (MODE_S && hasInlineStage1Assets(stage1Data)) {
    setStatus(statusElement, '素材仍是本地 base64，缺少后端 key/url，请先返回环节 1 重新上传。', 'error');
    stage2InFlight = false;
    setStage2ButtonsDisabled(false);
    return null;
  }


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

    syncStage2PreviewStateFromStage1(stage1Data);
    stage2LastSourceSignatures = buildStage2FormStateSignatures({
      stage1Data,
      bottomRequestState: buildPoster2BottomRequestState(stage1Data),
      copyOptimization: ensurePoster2CopyOptimizationState(),
      adjustments: stage2State.adjustments || {},
    });

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
          const imagesReady = await waitForImagesReady(posterLayoutRoot, 5000);
          const fontsReady = await waitForFontsReady(4000);
          if (!imagesReady || !fontsReady) {
            setStatus(
              statusElement,
              '截图准备超时，可能存在未加载资源。',
              'warning'
            );
          }
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
          ? App.utils.assetUrl(`templates/${entryPreview}`)
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
          templatePoster: fallbackPoster,
          promptGroup,
          promptBundleGroup,
          promptBundlePre,
          emailGroup,
          promptTextarea,
          emailTextarea,
          generateButton,
          regenerateButton,
          nextButton,
          generatedImage: null,
          disablePosterImage: true,
          promptManager,
          updatePromptPanels,
          promptPresets,
          latestPromptState,
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

    const defaultNotify = (msg) => {
      // 默认降级到 console，实际项目请传入 Toast/Modal 组件
      console.info(msg);
    };
    
    async function handleABTest({
      openABModal,
      baseline,
      generated,
      notify = defaultNotify,
      messages = {
        disabled: 'Demo 1.0: A/B preview is disabled.',
        ready: '已准备好最新生成结果，可在右侧预览卡片查看。'
      }
    } = {}) {
      // 先通知（非阻塞）
      notify(messages.disabled);
    
      try {
        // 支持 openABModal 为 undefined、同步返回值或返回 Promise
        const result = openABModal?.(baseline, generated);
        const opened = result instanceof Promise ? await result : result;
    
        if (!opened) {
          notify(messages.ready);
        }
    
        return Boolean(opened);
      } catch (err) {
        // 出错时记录并降级提示
        console.error('handleABTest error:', err);
        notify(messages.ready);
        return false;
      }
    }


   

    if (!MODE_S) {
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
    }

    if (MODE_S && document.getElementById('prompt-inspector')) {
      void (async () => {
        try {
          await hydrateModeSPresetDropdowns();
          // MODE_S 也必须初始化 prompt inspector，否则 Advanced 文本框不会被写入
          const stage1Data = loadStage1Data();
          await setupPromptInspector(stage1Data);
        } catch (e) {
          console.warn('[stage2] MODE_S preset hydrate failed', e);
        }
      })();
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

    stage2RunGeneration = (extra = {}) =>
      triggerGeneration({
        stage1Data,
        statusElement,
        posterOutput,
        aiPreview,
        aiSpinner,
        aiPreviewMessage,
        templatePoster: MODE_S ? null : templateState.poster,
        promptBundleGroup: MODE_S ? null : promptBundleGroup,
        promptBundlePre: MODE_S ? null : promptBundlePre,
        promptGroup: MODE_S ? null : promptGroup,
        emailGroup,
        promptTextarea: MODE_S ? null : promptTextarea,
        emailTextarea,
        generateButton,
        regenerateButton,
        nextButton,
        promptManager: MODE_S ? null : promptManager,
        updatePromptPanels: MODE_S ? null : updatePromptPanels,
        ...extra,
      });
    bindStage2GenerateButtonsOnce();
    updateRegenerateButtonState();

    if (promptInspector) {
      promptInspector.addEventListener('input', updateRegenerateButtonState);
      promptInspector.addEventListener('change', updateRegenerateButtonState);
    }

    nextButton.addEventListener('click', async () => {
      const stored = await loadStage2Result();
      if (!stored || !stored.final_poster) {
        setStatus(statusElement, '请先完成海报生成，再前往环节 3。', 'warning');
        return;
      }
      window.location.href = buildStage3Url(stored.poster_key || getPosterKeyFromLocation());
    });
  })();
}
function populateStage1Summary(stage1Data, overviewList, templateName) {
  if (!overviewList) return;
  overviewList.innerHTML = '';

  if (isTemplateBStage1Data(stage1Data)) {
    const materials = normaliseTemplateBMaterials(stage1Data);
    const entries = [
      ['模板', templateName || TEMPLATE_B_ID],
      ['品牌 / 代理', `${stage1Data.brand_name || ''} ｜ ${stage1Data.agent_name || ''}`],
      ['标题', stage1Data.title || ''],
      ['副标题', stage1Data.subtitle || ''],
      ['SKU', stage1Data.sku_text || ''],
      ['描述标题', stage1Data.description_title || stage1Data.descriptionTitle || ''],
      ['描述正文', stage1Data.description_body || stage1Data.descriptionBody || ''],
      ['主产品图', stage1Data.product_image_1 ? 'ready' : 'missing'],
      ['辅图 / supporting detail', stage1Data.product_image_2 ? 'ready' : 'optional'],
      ['辅图证据条', `${materials.length} 项素材`],
    ];

    entries.forEach(([term, description]) => {
      const dt = document.createElement('dt');
      dt.textContent = term;
      const dd = document.createElement('dd');
      dd.textContent = description;
      overviewList.appendChild(dt);
      overviewList.appendChild(dd);
    });
    return;
  }

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
  const directUrl = result?.final_url;
  if (typeof directUrl === 'string' && directUrl.trim()) {
    return directUrl.trim();
  }
  const url = result?.final_poster?.url;
  if (typeof url === 'string' && url.trim()) {
    return url.trim();
  }
  return null;
}

function normaliseFinalPosterPayload(result) {
  if (result?.final_poster && (result.final_poster.url || result.final_poster.key || result.final_poster.storage_key)) {
    return result.final_poster;
  }
  if (typeof result?.final_url === 'string' && result.final_url.trim()) {
    return {
      filename: `${result.trace_id || 'poster2'}-final.png`,
      media_type: inferImageMediaType(result.final_url) || 'image/png',
      width: null,
      height: null,
      storage_key: result.trace_id || createId(),
      url: result.final_url.trim(),
      key: null,
    };
  }
  return null;
}

function getPosterKeyFromLocation() {
  try {
    const url = new URL(window.location.href);
    return url.searchParams.get('poster_key') || '';
  } catch (error) {
    return '';
  }
}

function buildStage3Url(posterKey) {
  if (!posterKey) return 'stage3.html';
  return `stage3.html?poster_key=${encodeURIComponent(posterKey)}`;
}

function syncPosterKeyInLocation(posterKey) {
  if (!posterKey || typeof window === 'undefined') return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('poster_key', posterKey);
    window.history.replaceState({}, '', url.toString());
  } catch (error) {
    console.warn('Unable to sync poster_key into Stage 2 URL', error);
  }
}

function setPoster2Link(id, url) {
  const link = document.getElementById(id);
  if (!link) return;
  if (typeof url === 'string' && url.trim()) {
    link.href = url.trim();
    link.classList.remove('hidden');
  } else {
    link.removeAttribute('href');
    link.classList.add('hidden');
  }
}

function updatePoster2DiagnosticsPanel(data) {
  const setCode = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value == null || value === '' ? 'N/A' : String(value);
  };
  const setJson = (id, value, fallback) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (value == null) {
      el.textContent = fallback;
      return;
    }
    if (Array.isArray(value) && value.length === 0) {
      el.textContent = '[]';
      return;
    }
    if (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0) {
      el.textContent = '{}';
      return;
    }
    try {
      el.textContent = JSON.stringify(value, null, 2);
    } catch (_err) {
      el.textContent = fallback;
    }
  };

  setCode('poster2-template-id', data?.template_id || 'N/A');
  setCode('poster2-renderer-mode-requested', data?.renderer_mode || 'N/A');
  setCode('poster2-render-engine-used', data?.render_engine_used || 'N/A');
  setCode('poster2-degraded', typeof data?.degraded === 'boolean' ? String(data.degraded) : 'N/A');
  setCode('poster2-structure-complete', typeof data?.structure_complete === 'boolean' ? String(data.structure_complete) : 'N/A');
  setCode('poster2-incomplete-structure', typeof data?.incomplete_structure === 'boolean' ? String(data.incomplete_structure) : 'N/A');
  setCode('poster2-deliverable', typeof data?.deliverable === 'boolean' ? String(data.deliverable) : 'N/A');
  setCode('poster2-fallback-reason-code', data?.fallback_reason_code || 'N/A');
  setCode('poster2-foreground-renderer', data?.foreground_renderer || 'N/A');
  setCode('poster2-total-ms', data?.timings_ms?.total_ms ?? 'N/A');
  setCode('poster2-template-contract-version', data?.template_contract_version || 'N/A');
  setJson('poster2-missing-mandatory-regions', data?.missing_mandatory_regions, '[]');
  setJson('poster2-missing-required-slots', data?.missing_required_slots, '[]');
  setJson('poster2-region-render-status', data?.region_render_status, '{}');
  setJson('poster2-slot-binding-status', data?.slot_binding_status, '{}');
  setJson('poster2-template-behavior', data?.template_behavior, '{}');
  setJson('poster2-geometry-evidence', data?.geometry_evidence, '{}');
  setJson('poster2-bottom-contract-review', data?.bottom_contract_review, '{}');
  setJson('poster2-title-text-layer', data?.title_text_layer, 'null');
  setJson('poster2-subtitle-text-layer', data?.subtitle_text_layer, 'null');
  setJson('poster2-header-text-layer', data?.header_text_layer, 'null');
  setJson('poster2-header-contract-review', data?.header_contract_review, '{}');
  setJson('poster2-hero-contract-review', data?.hero_contract_review, '{}');
  setJson('poster2-product-contract-review', data?.product_contract_review, '{}');
  setJson('poster2-feature-contract-review', data?.feature_contract_review, '{}');
  setJson('poster2-product-annotation-contract-review', data?.product_annotation_contract_review, '{}');
  setJson('poster2-scenario-contract-review', data?.scenario_contract_review, '{}');
  setJson('poster2-copy-optimization-review', data?.copy_optimization_review, '{}');
  setJson('poster2-visible-truth-evidence', data?.visible_truth_evidence, '{}');
  setJson('poster2-template-b-parity-review', data?.template_b_parity_review, '{}');

  setPoster2Link('poster2-link-background', data?.debug_artifacts?.background_layer_url || data?.background_url || '');
  setPoster2Link('poster2-link-product-material', data?.debug_artifacts?.product_material_layer_url || '');
  setPoster2Link('poster2-link-foreground', data?.debug_artifacts?.foreground_layer_url || data?.foreground_url || '');
  setPoster2Link('poster2-link-final', data?.debug_artifacts?.final_composited_url || data?.final_url || '');
  setPoster2Link('poster2-link-metadata', data?.debug_artifacts?.renderer_metadata_url || '');
  renderResolverLayoutPreview(data);
}

function renderResolverLayoutPreview(data) {
  const wrap = document.getElementById('poster2-resolver-canvas-wrap');
  const section = document.getElementById('poster2-resolver-layout-preview');
  if (!wrap || !section) return;

  const review = data?.bottom_contract_review;
  if (!review) {
    section.classList.add('hidden');
    return;
  }

  const metrics = review.behavior_policy?.layout_metrics || {};
  const bottomShellTop = metrics.bottom_shell_top;
  const bottomShellHeight = metrics.bottom_shell_height;

  if (bottomShellTop == null || !bottomShellHeight) {
    section.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');

  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', `0 ${bottomShellTop} 1024 ${bottomShellHeight}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('aria-hidden', 'true');

  const addRect = (x, y, w, h, fill, stroke) => {
    const el = document.createElementNS(NS, 'rect');
    el.setAttribute('x', x); el.setAttribute('y', y);
    el.setAttribute('width', w); el.setAttribute('height', h);
    el.setAttribute('fill', fill);
    if (stroke) { el.setAttribute('stroke', stroke); el.setAttribute('stroke-width', '4'); }
    svg.appendChild(el);
  };
  const addText = (x, y, content, fill) => {
    const el = document.createElementNS(NS, 'text');
    el.setAttribute('x', x); el.setAttribute('y', y);
    el.setAttribute('font-size', '20'); el.setAttribute('font-family', 'monospace');
    el.setAttribute('fill', fill || '#334155');
    el.textContent = content;
    svg.appendChild(el);
  };

  // Bottom shell background
  addRect(0, bottomShellTop, 1024, bottomShellHeight, '#f8fafc', '#cbd5e1');

  // title_band_region
  const tb = review.title_band_region?.bounds;
  if (tb) {
    addRect(tb.x, tb.y, tb.w, tb.h, 'rgba(59,130,246,0.08)', '#93c5fd');
    addText(tb.x + 8, tb.y + 18, 'title_band_region', '#3b82f6');
  }

  // gallery_strip_region
  const gs = review.gallery_strip_region?.bounds;
  if (gs && gs.h > 0) {
    addRect(gs.x, gs.y, gs.w, gs.h, 'rgba(34,197,94,0.08)', '#86efac');
    addText(gs.x + 8, gs.y + 18, 'gallery_strip_region', '#16a34a');
  }

  // title_slot
  const tsY = metrics.title_slot_y;
  const tsH = metrics.title_slot_height;
  const tsX = tb?.x ?? 112;
  const tsW = tb?.w ?? 800;
  if (tsY != null && tsH != null) {
    addRect(tsX, tsY, tsW, tsH, 'rgba(59,130,246,0.22)', '#3b82f6');
    addText(tsX + 8, Math.max(tsY + 18, tsY + tsH - 6), `title_slot  y=${tsY}  h=${tsH}`, '#1d4ed8');
  }

  // subtitle_slot (only when not collapsed)
  const ssY = metrics.subtitle_slot_y;
  const ssH = metrics.subtitle_slot_height;
  const subtitleCollapsed = review.subtitle_slot?.state === 'collapsed';
  if (ssY != null && ssH != null && !subtitleCollapsed) {
    addRect(152, ssY, 720, ssH, 'rgba(20,184,166,0.22)', '#14b8a6');
    addText(160, Math.max(ssY + 18, ssY + ssH - 6), `subtitle_slot  y=${ssY}  h=${ssH}`, '#0f766e');
  }

  // gallery item slots
  const gallerySlots = review.gallery_slots || {};
  const itemColors = ['#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
  Object.entries(gallerySlots)
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([key, slot], i) => {
      const b = slot?.bounds;
      if (!b || slot.state === 'collapsed') return;
      const color = itemColors[i % itemColors.length];
      addRect(b.x, b.y, b.w, b.h, 'rgba(245,158,11,0.15)', color);
      addText(b.x + 4, b.y + 18, key.replace('gallery_item_slot_', 'g'), color);
    });

  wrap.innerHTML = '';
  wrap.appendChild(svg);

  // Summary table
  const table = document.getElementById('poster2-resolver-slot-table');
  if (table) {
    const requestedMode = review.requested_bottom_mode ?? 'N/A';
    const effectiveMode = review.bottom_mode ?? 'N/A';
    const modeRemapped = review.bottom_mode_remapped;
    const modeDisplay = modeRemapped
      ? `${requestedMode} → ${effectiveMode} ⚠`
      : effectiveMode;
    const rows = [
      ['requested_mode', requestedMode],
      ['effective_mode', modeDisplay],
      ['gallery_mode', review.gallery_mode],
      ['bottom_shell_top', bottomShellTop],
      ['bottom_shell_height', bottomShellHeight],
      ['title_slot_y / h', `${metrics.title_slot_y ?? 'N/A'} / ${metrics.title_slot_height ?? 'N/A'}`],
      ['subtitle_slot_y / h', subtitleCollapsed ? 'collapsed' : `${metrics.subtitle_slot_y ?? 'N/A'} / ${metrics.subtitle_slot_height ?? 'N/A'}`],
      ['visible_items', review.gallery_strip_region?.visible_item_count ?? 'N/A'],
    ];
    table.innerHTML = rows.map(([k, v]) =>
      `<div class="poster2-resolver-slot-row"><dt>${k}</dt><dd>${v}</dd></div>`
    ).join('');
  }
}

function renderPoster2RunHistory() {
  const root = document.getElementById('poster2-run-history-list');
  if (!root) return;
  root.innerHTML = '';
  const history = Array.isArray(stage2State.poster2.history) ? stage2State.poster2.history : [];
  history.forEach((entry, index) => {
    const card = document.createElement('div');
    card.className = 'poster2-run-entry';
    card.innerHTML = `
      <strong>Run ${history.length - index}</strong>
      <div>requested <code>${entry.requestedRenderer || 'N/A'}</code> -> effective <code>${entry.effectiveRenderer || 'N/A'}</code></div>
      <div>degraded <code>${entry.degraded}</code> fallback <code>${entry.fallbackReason || 'null'}</code></div>
      <div>incomplete_structure <code>${entry.incompleteStructure}</code> deliverable <code>${entry.deliverable}</code></div>
    `;
    if (entry.finalUrl) {
      const link = document.createElement('a');
      link.href = entry.finalUrl;
      link.target = '_blank';
      link.rel = 'noreferrer';
      link.className = 'poster-preview-link';
      link.textContent = 'Open final output';
      card.appendChild(link);
    }
    root.appendChild(card);
  });
}

function recordPoster2PilotRun(data) {
  const history = Array.isArray(stage2State.poster2.history) ? stage2State.poster2.history : [];
  history.unshift({
    requestedRenderer: data?.renderer_mode || null,
    effectiveRenderer: data?.render_engine_used || null,
    degraded: typeof data?.degraded === 'boolean' ? String(data.degraded) : 'N/A',
    incompleteStructure: typeof data?.incomplete_structure === 'boolean' ? String(data.incomplete_structure) : 'N/A',
    deliverable: typeof data?.deliverable === 'boolean' ? String(data.deliverable) : 'N/A',
    fallbackReason: data?.fallback_reason_code || null,
    finalUrl: extractVertexPosterUrl(data),
  });
  stage2State.poster2.history = history.slice(0, 6);
  renderPoster2RunHistory();
}


function renderPosterResult() {
  const root = document.getElementById('poster-result');
  if (!root) return;

  const { poster, assets } = stage2State;
  const fallbackWarning = document.getElementById('asset-fallback-warning');
  if (fallbackWarning) {
    fallbackWarning.textContent = '';
    fallbackWarning.classList.add('hidden');
  }

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
    applyImageWithFallback(
      scenarioImg,
      [src, DEFAULT_SCENARIO_ASSET, LOCAL_PLACEHOLDER_IMAGE, placeholderImages.scenario],
      fallbackWarning
    );
  }

  const productImg = document.getElementById('poster-result-product-image');
  const productSecondaryWrap = document.getElementById('poster-result-product-secondary-wrap');
  const productSecondaryImg = document.getElementById('poster-result-product-secondary-image');

  const titleEl = document.getElementById('poster-result-title');
  const subtitleEl = document.getElementById('poster-result-subtitle');
  const featureList = document.getElementById('poster-result-feature-list');
  const galleryEl = document.getElementById('poster-result-gallery');
  const headline =
    poster?.headline ||
    poster?.title ||
    poster?.copy?.headline ||
    '';
  const subheadline =
    poster?.subheadline ||
    poster?.subtitle ||
    poster?.tagline ||
    poster?.copy?.subheadline ||
    '';
  const features = stage2State.adjustments?.showBullets !== false
    ? (poster.features || [])
    : [];
  const galleryItems = (Array.isArray(poster.gallery_entries) ? poster.gallery_entries : [])
    .slice(0, 4)
    .map((entry, index) => ({
      src: assets.gallery_urls?.[index] || resolvePreviewAssetSrc(entry?.asset) || '',
      caption:
        entry?.caption ||
        entry?.title ||
        (poster.series?.[index] && poster.series[index].name) ||
        getModeSDefaultGalleryCaption(index),
    }));
  const previewModel = buildTemplateAPreviewModel({
    brandName: poster.brand_name || '待生成',
    agentName: poster.agent_name || '待生成',
    title: headline,
    subtitle: subheadline,
    features: features.slice(0, 3),
    logoSrc: assets.brand_logo_url || '',
    scenarioSrc: assets.scenario_url || '',
    productPrimarySrc: assets.product_url || '',
    productSecondarySrc: resolvePreviewAssetSrc(lastStage1Data?.product_image_2),
    galleryItems,
    bottomMode:
      stage2State.poster2?.latestResult?.bottom_contract_review?.effective_bottom_mode ||
      stage2State.poster2?.latestResult?.bottom_contract_review?.bottom_mode ||
      stage2State.poster2?.bottomContract?.bottomMode ||
      'title_gallery_split',
    galleryMode:
      stage2State.poster2?.latestResult?.bottom_contract_review?.gallery_mode ||
      stage2State.poster2?.bottomContract?.galleryMode ||
      'strip_local_visible_only',
    latestResult: stage2State.poster2?.latestResult || null,
  });
  applyTemplateAPreviewModel({
    root,
    brandLogoEl: logoImg,
    brandNameEl,
    agentNameEl,
    scenarioImageEl: scenarioImg,
    productImageEl: productImg,
    productSecondaryImageEl: productSecondaryImg,
    productSecondaryWrapEl: productSecondaryWrap,
    featureListEl: featureList,
    titleEl,
    subtitleEl,
    galleryEl,
    model: previewModel,
    galleryPlaceholderLabel: MATERIAL_DEFAULT_LABELS.gallery,
  });

  if (productImg) {
    applyImageWithFallback(
      productImg,
      [previewModel.productPrimarySrc, LOCAL_PLACEHOLDER_IMAGE, placeholderImages.product],
      fallbackWarning
    );
  }
  if (previewModel.truth?.showSecondaryInset && productSecondaryImg && previewModel.productSecondarySrc) {
    applyImageWithFallback(
      productSecondaryImg,
      [previewModel.productSecondarySrc, previewModel.productPrimarySrc, LOCAL_PLACEHOLDER_IMAGE, placeholderImages.productAlt],
      fallbackWarning
    );
  }
  if (galleryEl && previewModel.truth?.galleryVisible) {
    Array.from(galleryEl.querySelectorAll('figure img')).forEach((img, index) => {
      applyImageWithFallback(
        img,
        [
          previewModel.galleryItems[index]?.src || '',
          previewModel.logoSrc || '',
          LOCAL_PLACEHOLDER_IMAGE,
          placeholderImages.product,
        ],
        fallbackWarning
      );
    });
  }
}

function updateGenerationMetaPanel(data) {
  const recipeEl = document.getElementById('gen-meta-recipe');
  const seedEl = document.getElementById('gen-meta-seed');
  const fallbackEl = document.getElementById('gen-meta-fallback');
  const fallbackReasonEl = document.getElementById('gen-meta-fallback-reason');
  const gateEl = document.getElementById('gen-meta-gate');

  const recipe = data?.recipe_id || data?.meta?.recipe_id || 'N/A';
  const seed = data?.seed || data?.meta?.seed || 'N/A';
  const fallbackUsed =
    typeof data?.fallback_used === 'boolean'
      ? String(data.fallback_used)
      : data?.meta?.fallback_used ?? 'N/A';
  const fallbackReason =
    data?.fallback_reason || data?.meta?.fallback_reason || 'N/A';
  const gateSummary = data?.gate_summary || data?.meta?.gate_summary || 'N/A';

  if (recipeEl) recipeEl.textContent = recipe;
  if (seedEl) seedEl.textContent = seed;
  if (fallbackEl) fallbackEl.textContent = fallbackUsed;
  if (fallbackReasonEl) fallbackReasonEl.textContent = fallbackReason;
  if (gateEl) gateEl.textContent = gateSummary;
}

function updateStage2Warnings(data) {
  const warningElement = document.getElementById('stage2-warning');
  if (!warningElement) return;

  const warnings = [];
  const rawWarnings = data?.prompt_details?.warnings || data?.warnings || '';
  if (typeof rawWarnings === 'string' && rawWarnings.trim()) {
    rawWarnings.split(',').forEach((item) => {
      const token = item.trim();
      if (!token) return;
      if (token === 'vertex_quota_exhausted_fallback') {
        warnings.push('配额受限，已使用本地兜底渲染。');
      } else if (token === 'vertex_edit_failed_fallback') {
        warnings.push('AI 编辑失败，已使用本地兜底渲染。');
      } else if (token === 'kitposter1_locked_frame_fallback') {
        warnings.push('已使用锁版模板兜底渲染。');
      } else if (token === 'vertex_unavailable_fallback') {
        warnings.push('Vertex 未启用，已使用本地兜底渲染。');
      } else {
        warnings.push(token);
      }
    });
  }
  if (data?.fallback_used) {
    warnings.push('已触发 fallback。');
  }
  if (data?.degraded) {
    const reason = data?.degraded_reason ? `?${data.degraded_reason}?` : '';
    warnings.push(`????????${reason}`);
  }

  if (!warnings.length) {
    warningElement.classList.add('hidden');
    warningElement.textContent = '';
    return;
  }

  warningElement.textContent = `提示：${warnings.join(' ')}`;
  warningElement.classList.remove('hidden');
}


function applyVertexPosterResult(data) {
  console.log('[triggerGeneration] applyVertexPosterResult', data);
  stage2State.poster2.latestResult = data || null;
  ensurePoster2CopyOptimizationState().latestReview = data?.copy_optimization_review || null;
  renderPoster2CopyOptimizationReview(data?.copy_optimization_review || null);

  if (typeof updateStage2Warnings === 'function') {
    updateStage2Warnings(data);
  }

  const finalPoster = normaliseFinalPosterPayload(data);
  const finalPosterUrl = extractVertexPosterUrl(data);
  const finalImg = document.getElementById('final-poster-img');
  const finalPlaceholder = document.getElementById('final-poster-placeholder');
  const finalLink = document.getElementById('final-poster-link');
  const finalKey = document.getElementById('final-poster-key');
  const copyButton = document.getElementById('final-poster-copy');

  if (finalPosterUrl && finalImg) {
    finalImg.src = finalPosterUrl;
    finalImg.classList.remove('hidden');
    if (finalPlaceholder) finalPlaceholder.classList.add('hidden');
    if (finalLink) {
      finalLink.href = finalPosterUrl;
      finalLink.classList.remove('hidden');
    }
  } else {
    if (finalImg) {
      finalImg.removeAttribute('src');
      finalImg.classList.add('hidden');
    }
    if (finalPlaceholder) finalPlaceholder.classList.remove('hidden');
    if (finalLink) finalLink.classList.add('hidden');
  }

  if (finalKey) {
    finalKey.textContent =
      finalPoster?.key || finalPoster?.storage_key || data?.trace_id || 'N/A';
  }

  if (copyButton) {
    copyButton.onclick = async () => {
      if (!finalPosterUrl) return;
      try {
        await navigator.clipboard.writeText(finalPosterUrl);
        copyButton.textContent = 'Copied';
        setTimeout(() => {
          copyButton.textContent = 'Copy URL';
        }, 1200);
      } catch (error) {
        console.warn('????', error);
      }
    };
  }

  if (typeof updateGenerationMetaPanel === 'function') {
    updateGenerationMetaPanel(data);
  }
  updatePoster2DiagnosticsPanel(data);
  if (data?.template_id === POSTER2_PILOT_TEMPLATE_ID) {
    recordPoster2PilotRun(data);
  }
  renderPosterResult();
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

async function buildModeSGalleryItems(stage1, apiCandidates) {
  return [];
}

function formatPosterGenerationError(error) {
  const rawDetail = error?.responseJson?.detail ?? error?.responseJson ?? null;

  if (Array.isArray(rawDetail)) {
    const first = rawDetail.find((entry) => entry?.msg || entry?.message);
    if (first?.msg) {
      const loc = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : null;
      if (loc && first?.type === 'string_too_long' && first?.ctx?.max_length) {
        return `${loc} exceeds max length ${first.ctx.max_length}`;
      }
      return loc ? `${loc}: ${first.msg}` : first.msg;
    }
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
    templatePoster = null,
    promptBundleGroup,
    promptBundlePre,
    promptGroup, emailGroup, promptTextarea, emailTextarea,
    generateButton, regenerateButton, nextButton,
    promptManager, updatePromptPanels, promptPresets, latestPromptState,
    forceVariants = null, abTest = false,
  } = opts;
  const { disablePosterImage = false } = opts;
  const liveStage1Data = loadStage1Data() || stage1Data || lastStage1Data || {};
  const requestStage1Data = cloneStage2Value(liveStage1Data) || {};
  syncPoster2BottomContractFromControls(requestStage1Data);
  const bottomRequestState = cloneStage2Value(buildPoster2BottomRequestState(requestStage1Data));
  const adjustments = cloneStage2Value(stage2State.adjustments || {});
  const rendererMode = stage2State.poster2.rendererMode || 'auto';
  syncStage2PreviewStateFromStage1(requestStage1Data);
  const posterPreviewSection = document.getElementById('stage2-poster-preview-section');
  let didAttempt = false;
  const isRegenerate = !!opts.isRegenerate;
  stage2State.generationAction = isRegenerate ? 'regenerate' : 'generate';
  stage2State.regenPolicy = isRegenerate
    ? { updateScenario: true, updateGallery: true, updateProduct: false }
    : { updateScenario: false, updateGallery: false, updateProduct: false };
  if (stage2InFlight && stage2ActiveAbortController) {
    abortActiveStage2Request('superseded_by_new_generate');
    console.info('[stage2] aborted prior in-flight generate request');
  }
  const mySeq = ++stage2GenerationSeq;
  stage2ActiveRequestId = mySeq;
  stage2ActiveAbortController = new AbortController();
  stage2InFlight = true;
  setStage2ButtonsDisabled(true);
  const previousResponsePresence = {
    lastPosterResult: Boolean(lastPosterResult),
    latestResult: Boolean(stage2State.poster2.latestResult),
    rawResult: Boolean(posterGenerationState.rawResult),
    promptBundle: Boolean(posterGenerationState.promptBundle || lastPromptBundle),
    finalPosterImage: Boolean(posterGeneratedImage),
    vertexLastResponse: Boolean(stage2State.vertex.lastResponse),
    storedStage2Result: Boolean(sessionStorage.getItem(STORAGE_KEYS.stage2)),
    lastSuccessfulFormSignature: Boolean(stage2LastSuccessfulFormSignature),
  };
  const sourceInvalidation = invalidateStage2DerivedStateForSnapshot(requestStage1Data, {
    bottomRequestState,
    copyOptimizationState: ensurePoster2CopyOptimizationState(),
    adjustments,
  });
  const previousSuccessPresent = Object.values(previousResponsePresence).some(Boolean);
  const successSignatureMismatch = Boolean(
    stage2LastSuccessfulFormSignature &&
      sourceInvalidation.signatures?.formSignature &&
      stage2LastSuccessfulFormSignature !== sourceInvalidation.signatures.formSignature
  );
  const clearedSuccessState = clearStage2DerivedSurfacesBeforeRequest();
  renderPosterResult();
  const copyOptimizationState = cloneStage2Value(ensurePoster2CopyOptimizationState());
  console.info('[stage2] request source signatures', {
    request_id: mySeq,
    assets_changed: sourceInvalidation.assetsChanged,
    copy_changed: sourceInvalidation.copyChanged,
    bottom_changed: sourceInvalidation.bottomChanged,
    request_controls_changed: sourceInvalidation.requestControlsChanged,
    invalidated_fields: sourceInvalidation.invalidatedFields,
    last_success_signature_mismatch: successSignatureMismatch,
    cleared_success_state: clearedSuccessState,
  });

  // 1) 选可用 API 基址
  const apiCandidates = getApiCandidates(document.getElementById('api-base')?.value || null);
  if (!apiCandidates.length) {
    if (isCurrentStage2Request(mySeq)) {
      stage2InFlight = false;
      stage2ActiveAbortController = null;
      setStage2ButtonsDisabled(false);
    }
    setStatus(statusElement, '未找到可用后端，请先填写 API 基址。', 'warning');
    return null;
  }

  // 2) 资产“再水化”确保 dataUrl 就绪（仅用于画布预览；发送给后端使用 r2Key）
  await hydrateStage1DataAssets(requestStage1Data);
  if (!isCurrentStage2Request(mySeq)) return null;

  const usePoster2Pilot = shouldUsePoster2Pilot(requestStage1Data);
  let endpointPath = '/api/generate-poster';

  // 3) 主体 poster（素材必须已上云，仅传 URL/Key）
  const templateId = requestStage1Data.template_id;
  const sc = requestStage1Data.scenario_asset || null;
  const pd = requestStage1Data.product_asset || null;

  const scenarioMode = requestStage1Data.scenario_mode || 'upload';
  const productMode = requestStage1Data.product_mode || 'upload';

  let posterPayload;
  let brandLogoRef;
  let scenarioRef;
  let productRef;
  let galleryItems;
  let productImage1Ref;
  let productImage2Ref;
  let payload;
  try {
    if (MODE_S && templateId === TEMPLATE_B_ID) {
      const templateBRequest = await buildTemplateBPosterPayload(requestStage1Data, apiCandidates, { rendererMode });
      payload = templateBRequest.payload;
      brandLogoRef = templateBRequest.refs.logoRef;
      productImage1Ref = templateBRequest.refs.productRef;
      productImage2Ref = templateBRequest.refs.productSecondaryRef;
      galleryItems = [];
      endpointPath = '/api/v2/generate-poster';
      posterPayload = {
        template_id: payload.template_id,
        scenario_mode: null,
        product_mode: 'upload',
        features: [],
        gallery_items: [],
        brand_logo: payload.logo?.url || null,
        scenario_asset: null,
        product_asset: payload.product_image?.url || null,
        product_key: payload.product_image?.key || null,
        sku_text: payload.sku_text || null,
        description_title: payload.description_title || null,
        description_body: payload.description_body || null,
        materials_images: payload.materials_images || [],
      };
    } else if (usePoster2Pilot) {
      const poster2Request = await buildPoster2GeneratePayload(requestStage1Data, apiCandidates, {
        bottomRequestState,
        copyOptimizationState,
        adjustments,
        rendererMode,
      });
      payload = poster2Request.payload;
      brandLogoRef = poster2Request.refs.logoRef;
      productImage1Ref = poster2Request.refs.productRef;
      scenarioRef = poster2Request.refs.scenarioRef;
      galleryItems = (poster2Request.refs.galleryRefs || []).map((ref) => ({
        key: ref.key || null,
        asset: ref.url || null,
        mode: 'upload',
      }));
      endpointPath = '/api/v2/generate-poster';
      posterPayload = {
        template_id: payload.template_id,
        scenario_mode: 'upload',
        product_mode: 'upload',
        features: payload.features || [],
        gallery_items: galleryItems,
        brand_logo: payload.logo?.url || null,
        scenario_asset: payload.scenario_image?.url || null,
        scenario_key: payload.scenario_image?.key || null,
        product_asset: payload.product_image?.url || null,
        product_key: payload.product_image?.key || null,
      };
    } else if (MODE_S) {
      const safeText = (value, fallback) => {
        const text = typeof value === 'string' ? value.trim() : '';
        return text || fallback;
      };

      productImage1Ref = await normaliseAssetReference(requestStage1Data.product_image_1, {
        field: 'poster.product_image_1',
        required: true,
        apiCandidates,
        folder: 'product',
      });
      productImage2Ref = await normaliseAssetReference(requestStage1Data.product_image_2, {
        field: 'poster.product_image_2',
        required: false,
        apiCandidates,
        folder: 'product',
      }, productImage1Ref);
      scenarioRef = await normaliseAssetReference(requestStage1Data.scenario_asset, {
        field: 'poster.scenario_asset',
        required: false,
        apiCandidates,
        folder: 'scenario',
      }, productImage1Ref);

      const scenarioCandidate = requestStage1Data.scenario_asset || requestStage1Data.scenario_image;
      scenarioRef = await normaliseAssetReference(scenarioCandidate, {
        field: 'poster.scenario_asset',
        required: false,
        apiCandidates,
        folder: 'scenario',
      }, productImage1Ref);

      const showBullets = adjustments?.showBullets !== false;
      const bullets = Array.isArray(requestStage1Data.bullets)
        ? requestStage1Data.bullets.filter(Boolean)
        : [];
      const title = safeText(requestStage1Data.title, 'Poster');
      const channel = safeText(requestStage1Data.channel, 'direct');
      const intent = safeText(requestStage1Data.intent, 'default');
      const brandName = safeText(requestStage1Data.brand_name, 'Brand');
      const productName = safeText(requestStage1Data.product_name, title);
      const promo = safeText(requestStage1Data.promo, '');
      const price = safeText(requestStage1Data.price, '');
      const tagline = safeText(requestStage1Data.tagline || requestStage1Data.promo || requestStage1Data.price, '');
      const subtitle = safeText(tagline, title);
      const seriesDescription = safeText(
        requestStage1Data.promo || requestStage1Data.price || requestStage1Data.intent,
        title
      );
      const agentName = resolveModeSAgentName(requestStage1Data.agent_name || channel, brandName);

      if (productImage1Ref?.url) {
        assertAssetUrl('product_image_1', productImage1Ref.url);
      }

      posterPayload = {
        brand_name: brandName,
        agent_name: agentName,
        scenario_image: scenarioRef?.key || scenarioRef?.url || null,
        product_name: productName,
        channel,
        intent,
        brand_color: requestStage1Data.brand_color || null,
        price: price || null,
        promo: promo || null,
        template_id: templateId || DEFAULT_STAGE1.template_id,
        features: showBullets ? bullets : [],
        title,
        subtitle,
        series_description: seriesDescription,
        product_image_1: productImage1Ref?.url || null,
        product_image_1_key: productImage1Ref?.key || null,
        product_image_2: productImage2Ref?.url || null,
        product_image_2_key: productImage2Ref?.key || null,
        product_key: productImage1Ref?.key || null,
        product_asset: productImage1Ref?.url || null,
        scenario_key: scenarioRef?.key || null,
        scenario_asset: scenarioRef?.url || null,
        scenario_mode: 'upload',
        product_mode: 'upload',
        gallery_items: [],
        gallery_label: null,
        gallery_limit: 0,
        gallery_allows_prompt: false,
        gallery_allows_upload: false,
      };
      console.log('[stage2] MODE_S poster payload (scenario)', {
        scenario_asset: posterPayload.scenario_asset,
        scenario_key: posterPayload.scenario_key,
      });
      console.log('[stage2] payload audit', {
        scenario_key: posterPayload?.scenario_key,
        scenario_asset: posterPayload?.scenario_asset,
        scenario_image: posterPayload?.scenario_image,
        product_image_1_key: posterPayload?.product_image_1_key,
        product_image_2_key: posterPayload?.product_image_2_key,
      });
    } else {
    brandLogoRef = await normaliseAssetReference(requestStage1Data.brand_logo, {
      field: 'poster.brand_logo',
      required: true,
      apiCandidates,
      folder: 'brand-logo',
    });

    scenarioRef = await normaliseAssetReference(sc, {
      field: 'poster.scenario_image',
      required: !MODE_S,
      apiCandidates,
      folder: 'scenario',
    }, brandLogoRef);

    productRef = await normaliseAssetReference(pd, {
      field: 'poster.product_image',
      required: true,
      apiCandidates,
      folder: 'product',
    }, brandLogoRef);

    galleryItems = await buildGalleryItemsWithFallback(requestStage1Data, brandLogoRef, apiCandidates, 4);

    const features = Array.isArray(requestStage1Data.features)
      ? requestStage1Data.features.filter(Boolean)
      : [];

    const brandLogoUrl = brandLogoRef.url || null;
    const scenarioUrl = scenarioRef?.url || null;
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
      brand_name: requestStage1Data.brand_name,
      agent_name: requestStage1Data.agent_name,
      scenario_image: scenarioUrl,
      product_name: requestStage1Data.product_name,
      channel: requestStage1Data.channel || null,
      intent: requestStage1Data.intent || null,
      template_id: templateId,
      features,
      title: requestStage1Data.title,
      subtitle: requestStage1Data.subtitle,
      series_description: requestStage1Data.series_description,

      brand_logo: brandLogoUrl,
      brand_logo_key: brandLogoRef.key,

      scenario_key: scenarioRef?.key || null,
      scenario_asset: scenarioUrl,

      product_key: productRef.key,
      product_asset: productUrl,

      scenario_mode: scenarioMode,
      scenario_prompt:
        scenarioMode === 'prompt'
          ? requestStage1Data.scenario_prompt || requestStage1Data.scenario_image || null
          : null,
      product_mode: productMode,
      product_prompt: productMode === 'prompt' ? requestStage1Data.product_prompt || null : null,

      gallery_items: galleryItems,
      gallery_label: requestStage1Data.gallery_label || null,
      gallery_limit: requestStage1Data.gallery_limit ?? null,
      gallery_allows_prompt: requestStage1Data.gallery_allows_prompt !== false,
      gallery_allows_upload: requestStage1Data.gallery_allows_upload !== false,
    };
    }
  } catch (error) {
    console.error('[triggerGeneration] asset normalisation failed', error);
    if (isCurrentStage2Request(mySeq)) {
      setStatus(
        statusElement,
        error instanceof Error ? error.message : '素材未完成上传，请先上传至 R2/GCS。',
        'error',
      );
      stage2InFlight = false;
      stage2ActiveAbortController = null;
      setStage2ButtonsDisabled(false);
    }
    return null;
  }
  // 4) Prompt bundle (Mode S presets only)
  const reqFromInspector = MODE_S ? {} : (promptManager?.buildRequest?.() || {});
  if (!MODE_S && forceVariants != null) reqFromInspector.variants = forceVariants;

  // Template B does not use Family A prompt slots — skip bundle to avoid sending A-family prompts.
  const isTemplateBRequest = MODE_S && requestStage1Data.template_id === TEMPLATE_B_ID;
  let promptBundleStrings = isTemplateBRequest
    ? null
    : MODE_S
      ? await buildModeSPromptBundle(requestStage1Data)
      : buildPromptBundleStrings(reqFromInspector.prompts || {});
  if (!MODE_S && isPromptBundleEmpty(promptBundleStrings)) {
    const fallbackState = latestPromptState?.slots
      ? latestPromptState
      : createPromptState(requestStage1Data, promptPresets || { presets: {}, defaultAssignments: {} });
    promptBundleStrings = serialisePromptState(fallbackState);
  }
  if (!isCurrentStage2Request(mySeq)) return null;

  if (!payload) {
    const renderMode = MODE_S ? MODE_S_RENDER_MODE : (stage2State.renderMode || 'kitposter1_a');
    const requestBase = {
      poster: posterPayload,
      render_mode: renderMode,
      variants: MODE_S ? 1 : clampVariants(reqFromInspector.variants ?? 1),
      seed: MODE_S ? 0 : (reqFromInspector.seed ?? null),
      lock_seed: MODE_S ? true : !!reqFromInspector.lockSeed,
    };

      payload = { ...requestBase };
    if (promptBundleStrings) {
      payload.prompt_bundle = promptBundleStrings;
    }
    // Template B (template_product_sheet_v1) does not use KitPosterDraft — omit draft
    // to avoid backend schema rejection (KitPosterDraft.template_id is Literal family-A only).
    if (MODE_S && requestStage1Data.template_id !== TEMPLATE_B_ID) {
      payload.draft = buildKitPosterDraftFromSource(
        requestStage1Data,
        adjustments,
        renderMode
      );
    }
  }

  if (!isCurrentStage2Request(mySeq)) return null;
  payload = freezeStage2RequestSnapshot(cloneStage2Value(payload));
  updateDebugPanels({ draft: stage2State.draft, payload: cloneStage2Value(payload) });
  const requestPayloadSignature = hashStage2StableValue(payload);
  const preflightDiagnostics = buildStage2PreflightDiagnostics({
    requestId: mySeq,
    formSignatures: sourceInvalidation.signatures,
    payload,
    previousSuccessPresent,
    invalidatedFields: sourceInvalidation.invalidatedFields || [],
    clearedSuccessState,
    detectedGalleryItems: sourceInvalidation.signatures?.bottom?.requested_gallery_count || 0,
  });
  console.info('[stage2] generate preflight', preflightDiagnostics);
  logStage2RequestBoundary({
    requestId: mySeq,
    currentUiValues: readStage2OperatorUiValues(),
    canonicalFormState: {
      assets: sourceInvalidation.signatures?.assets || null,
      copy: sourceInvalidation.signatures?.copy || null,
      bottom: sourceInvalidation.signatures?.bottom || null,
      copyReviewAcceptance: sourceInvalidation.signatures?.copyReviewAcceptance || null,
      requestControls: sourceInvalidation.signatures?.requestControls || null,
    },
    requestSnapshot: endpointPath === '/api/v2/generate-poster'
      ? buildPoster2RequestSummary(payload)
      : cloneStage2Value(payload),
    previousResponsePresence,
    invalidatedFields: sourceInvalidation.invalidatedFields || [],
    preflightDiagnostics,
  });

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
    gallery: (posterPayload.gallery_items || []).map((item, index) => ({
      index,
      mode: item.mode,
      key: item.key || null,
      url: item.asset || null,
    })),
  };

  console.info('[triggerGeneration] prepared payload', {
    apiCandidates,
    endpointPath,
    poster: posterSummary,
    prompt_bundle: payload.prompt_bundle,
    variants: payload.variants,
    seed: payload.seed,
    lock_seed: payload.lock_seed,
  });
  if (endpointPath === '/api/v2/generate-poster') {
    console.info('[stage2][poster2] request summary', {
      request_id: mySeq,
      ...buildPoster2RequestSummary(payload),
      canonical_form_signature_hash: preflightDiagnostics.canonical_form_signature_hash,
      request_payload_signature_hash: requestPayloadSignature,
      content_type: 'application/json; charset=UTF-8',
    });
  }
  console.info('[triggerGeneration] asset audit', assetAudit);
  
  // 面板同步
  if (!MODE_S) {
    updatePromptPanels?.({ bundle: payload.prompt_bundle });
  }
  
  // 5) 体积守护
  const rawPayload = JSON.stringify(payload);
  try { validatePayloadSize(rawPayload); } catch (e) {
    if (isCurrentStage2Request(mySeq)) {
      setStatus(statusElement, e.message, 'error');
      stage2InFlight = false;
      stage2ActiveAbortController = null;
      setStage2ButtonsDisabled(false);
    }
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
  updateStage2Warnings(null);
  posterGeneratedImage = null;
  posterGeneratedLayout = TEMPLATE_DUAL_LAYOUT;
  if (promptGroup) promptGroup.classList.add('hidden');
  if (emailGroup) emailGroup.classList.add('hidden');
  if (nextButton) nextButton.disabled = true;

  let fallbackTriggered = false;
  let fallbackTimerId = null;
  const allowTemplateFallback = !MODE_S;

  const clearFallbackTimer = () => {
    if (fallbackTimerId) {
      clearTimeout(fallbackTimerId);
      fallbackTimerId = null;
    }
  };
  const enableTemplateFallback = async (message, options = {}) => {
    if (!allowTemplateFallback) return;
    if (fallbackTriggered) return;
    fallbackTriggered = true;
    clearFallbackTimer();

    if (aiPreview) aiPreview.classList.add('complete');
    if (aiSpinner) aiSpinner.classList.add('hidden');

    const nextPrompt = typeof options.prompt === 'string' ? options.prompt : '';
    const nextEmail = typeof options.email === 'string' ? options.email : '';
    const hasCopy = Boolean(nextPrompt.trim()) || Boolean(nextEmail.trim());
    const canProceed = MODE_S ? Boolean(templatePoster) : hasCopy;
    if (nextButton) nextButton.disabled = !canProceed;

    if (templatePoster && hasCopy) {
      try {
        await saveStage2Result({
          prompt: nextPrompt,
          email_body: nextEmail,
          prompt_bundle: options.prompt_bundle || null,
          final_poster: { ...templatePoster },
          poster_url: null,
          assets: { ...stage2State.assets },
          poster: { ...stage2State.poster },
          template_poster: { ...templatePoster },
          variants: [],
          seed: null,
          lock_seed: false,
          template_fallback: true,
          template_id: requestStage1Data.template_id || null,
        });
      } catch (error) {
        console.error('save template fallback failed', error);
      }
    }

    const statusLevel = hasCopy ? 'warning' : 'error';
    const statusMessage = message || (hasCopy
      ? '已使用模板海报兜底，可继续到环节 3。'
      : '生成失败，请重试。');
    setStatus(statusElement, statusMessage, statusLevel);
  };

  if (templatePoster && allowTemplateFallback) {
    fallbackTimerId = setTimeout(() => {
      void enableTemplateFallback();
    }, 60_000);
  }

  try {
    didAttempt = true;
    await warmUp(apiCandidates);
    if (!isCurrentStage2Request(mySeq)) return null;
    const resp = await postJsonWithRetry(apiCandidates, endpointPath, payload, 1, rawPayload, {
      signal: stage2ActiveAbortController?.signal,
    });
    const data = (resp && typeof resp.json === 'function') ? await resp.json() : resp;
    if (!isCurrentStage2Request(mySeq)) return null;

    lastPosterResult = data || null;
    updateDebugPanels({ response: data });
    lastPromptBundle = data?.prompt_bundle || null;
    posterGenerationState.promptBundle = data?.prompt_bundle || null;
    posterGenerationState.rawResult = data || null;
    posterGeneratedLayout = TEMPLATE_DUAL_LAYOUT;
    stage2LastSuccessfulFormSignature = sourceInvalidation.signatures?.formSignature || null;
    stage2LastSuccessfulRequestSignature = requestPayloadSignature;

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
      hasPoster: Boolean(data?.final_poster || data?.final_url),
      variants: Array.isArray(data?.variants) ? data.variants.length : 0,
      seed: data?.seed ?? null,
      lock_seed: data?.lock_seed ?? null,
      render_engine_used: data?.render_engine_used ?? null,
    });

    applyVertexPosterResult(data);

    clearFallbackTimer();

    if (aiPreview) aiPreview.classList.add('complete');
    if (aiSpinner) aiSpinner.classList.add('hidden');

    const nextPrompt = data?.prompt || '';
    const nextEmail = data?.email_body || '';
    if (emailTextarea) emailTextarea.value = nextEmail;
    if (promptTextarea) promptTextarea.value = nextPrompt;

    const hasCopy = Boolean(nextPrompt.trim()) || Boolean(nextEmail.trim());
    const canProceed = MODE_S ? Boolean(data?.final_poster || data?.final_url) : hasCopy;
    setStatus(
      statusElement,
      usePoster2Pilot
        ? '海报生成完成。'
        : hasCopy
        ? '文案已生成。'
        : '请求完成，但未返回文案。',
      usePoster2Pilot || hasCopy ? 'success' : 'warning',
    );

    if (nextButton) nextButton.disabled = !canProceed;
    generateButton.disabled = false;
    if (regenerateButton) regenerateButton.disabled = false;
    regenerateButton?.classList.remove('hidden');

    if (stage2State.generated) {
      stage2State.generated.lastCopy = {
        prompt: nextPrompt,
        email_body: nextEmail,
        prompt_bundle: data?.prompt_bundle || null,
      };
    }

    try {
      const finalPoster = normaliseFinalPosterPayload(data);
      if (!finalPoster || !(finalPoster.url || finalPoster.key || finalPoster.storage_key)) {
        setStatus(statusElement, '缺少 final_poster；Mode S 必须返回最终海报。', 'error');
        return null;
      }
      await saveStage2Result({
        poster_key: data?.poster_key || null,
        prompt: nextPrompt,
        email_body: nextEmail,
        prompt_bundle: data?.prompt_bundle || null,
        final_poster: { ...finalPoster },
        poster_url: null,
        assets: { ...stage2State.assets },
        poster: { ...stage2State.poster },
        template_poster: null,
        template_fallback: Boolean(data?.fallback_used),
        template_id: requestStage1Data.template_id || null,
        seed: data?.seed ?? null,
        lock_seed: data?.lock_seed ?? null,
      });
      syncPosterKeyInLocation(data?.poster_key || null);
    } catch (error) {
      console.error('save stage2 result failed', error);
    }

    stage2HasAttemptedGenerate = true;
    if (stage2State.generated) {
      stage2State.generated.attempted = true;
    }
    if (posterPreviewSection) {
      posterPreviewSection.classList.remove('hidden');
    }
    stage2LastGeneratedAssetFingerprint = fingerprintAssets(stage2State.assets);
    updateRegenerateButtonState();

    return data;
  } catch (error) {
    if (error?.name === 'AbortError') {
      console.info('[generatePoster] request aborted', { request_id: mySeq, message: error?.message || 'aborted' });
      return null;
    }
    if (!isCurrentStage2Request(mySeq)) return null;
    console.error('[generatePoster] request failed', {
      error,
      status: error?.status,
      responseJson: error?.responseJson,
      responseText: error?.responseText,
      request_id: mySeq,
      request_summary: endpointPath === '/api/v2/generate-poster' ? buildPoster2RequestSummary(payload) : null,
    });
    updateDebugPanels({
      response: error?.responseJson || error?.responseText || {
        message: error?.message || 'request_failed',
        status: error?.status || null,
      },
    });
    const detail = error?.responseJson?.detail || null;
    const quotaExceeded =
      error?.status === 429 &&
      (detail?.error === 'vertex_quota_exceeded' || detail === 'vertex_quota_exceeded');
    const friendlyMessage = quotaExceeded
      ? '图像生成额度已用尽，请稍后重试或上传已有素材。'
      : formatPosterGenerationError(error);
    const statusHint = typeof error?.status === 'number' ? ` (HTTP ${error.status})` : '';
    const decoratedMessage = `${friendlyMessage}${statusHint}`;
    setStatus(statusElement, decoratedMessage, 'error');
    generateButton.disabled = false;
    if (regenerateButton) regenerateButton.disabled = false;
    if (aiSpinner) aiSpinner.classList.add('hidden');
    if (aiPreview) aiPreview.classList.add('complete');
    refreshPosterLayoutPreview();

    const storedPrompt = stage2State.generated?.lastCopy?.prompt || '';
    const storedEmail = stage2State.generated?.lastCopy?.email_body || '';
    const currentPrompt = (promptTextarea?.value || '').trim();
    const currentEmail = (emailTextarea?.value || '').trim();
    const hasStoredCopy = Boolean(currentPrompt) || Boolean(currentEmail) || Boolean(storedPrompt) || Boolean(storedEmail);
    const canProceed = MODE_S ? Boolean(lastPosterResult?.final_poster) : hasStoredCopy;
    if (nextButton) nextButton.disabled = !canProceed;

    stage2HasAttemptedGenerate = true;
    if (stage2State.generated) {
      stage2State.generated.attempted = true;
    }
    if (posterPreviewSection) {
      posterPreviewSection.classList.remove('hidden');
    }
    renderPosterResult();
    updateRegenerateButtonState();
    return null;
  } finally {
    if (isCurrentStage2Request(mySeq)) {
      stage2InFlight = false;
      stage2ActiveAbortController = null;
      setStage2ButtonsDisabled(false);
      updateRegenerateButtonState();
    }
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

    const nested = [value.asset, value.image, value.poster_image, value.final_poster];
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
  if (!root || !data) return;
  root.innerHTML = `
    <div class="poster-preview poster-preview--result">
      <div class="poster-header">
        <div class="poster-logo">
          <div class="poster-logo-image"><img data-preview-role="brand-logo" alt="" /></div>
          <div class="poster-brand-name" data-preview-role="brand-name"></div>
        </div>
        <div class="poster-agent" data-preview-role="agent-name"></div>
      </div>
      <div class="poster-body">
        <div class="poster-left">
          <img data-preview-role="scenario-image" alt="" />
        </div>
        <div class="poster-right">
          <div class="poster-product-wrapper">
            <img data-preview-role="product-image" alt="" />
            <div data-preview-role="product-secondary-wrap" class="poster-product-secondary-wrap hidden">
              <img data-preview-role="product-secondary-image" alt="" />
            </div>
            <ul data-preview-role="feature-list" class="feature-tags">
              <li class="feature-tag feature-tag--top"><span></span></li>
              <li class="feature-tag feature-tag--middle"><span></span></li>
              <li class="feature-tag feature-tag--bottom"><span></span></li>
            </ul>
          </div>
        </div>
      </div>
      <div class="poster-title-block">
        <div data-preview-role="title" class="poster-title"></div>
        <div data-preview-role="subtitle" class="poster-subtitle"></div>
      </div>
      <div data-preview-role="gallery" class="poster-gallery"></div>
    </div>
  `;
  const previewRoot = root.firstElementChild;
  applyTemplateAPreviewModel({
    root: previewRoot,
    brandLogoEl: previewRoot?.querySelector('[data-preview-role="brand-logo"]'),
    brandNameEl: previewRoot?.querySelector('[data-preview-role="brand-name"]'),
    agentNameEl: previewRoot?.querySelector('[data-preview-role="agent-name"]'),
    scenarioImageEl: previewRoot?.querySelector('[data-preview-role="scenario-image"]'),
    productImageEl: previewRoot?.querySelector('[data-preview-role="product-image"]'),
    productSecondaryImageEl: previewRoot?.querySelector('[data-preview-role="product-secondary-image"]'),
    productSecondaryWrapEl: previewRoot?.querySelector('[data-preview-role="product-secondary-wrap"]'),
    featureListEl: previewRoot?.querySelector('[data-preview-role="feature-list"]'),
    titleEl: previewRoot?.querySelector('[data-preview-role="title"]'),
    subtitleEl: previewRoot?.querySelector('[data-preview-role="subtitle"]'),
    galleryEl: previewRoot?.querySelector('[data-preview-role="gallery"]'),
    model: data,
    galleryPlaceholderLabel: MATERIAL_DEFAULT_LABELS.gallery,
  });
}

function buildDualPosterData(stage1Data, generation) {
  const poster = generation?.poster || {};
  const galleryEntries = Array.isArray(stage1Data?.gallery_entries)
    ? stage1Data.gallery_entries.filter(Boolean)
    : [];
  const generationGallery = Array.isArray(poster.gallery_images)
    ? poster.gallery_images
    : Array.isArray(generation?.gallery_images)
    ? generation.gallery_images
    : [];
  const galleryItems = galleryEntries.slice(0, 4).map((entry, index) => ({
    src:
      resolveSlotAssetUrl(generationGallery[index]) ||
      resolveSlotAssetUrl(entry?.asset) ||
      '',
    caption: entry?.caption || entry?.title || getModeSDefaultGalleryCaption(index),
  }));
  return buildTemplateAPreviewModel({
    brandName: stage1Data?.brand_name || poster.brand_name || '',
    agentName: stage1Data?.agent_name || poster.agent_name || '',
    title: stage1Data?.title || poster.title || '',
    subtitle:
      resolveTemplateABottomSupportCopy(stage1Data, '') ||
      poster.subtitle ||
      '',
    features: resolveStage1ProductCallouts(stage1Data),
    logoSrc: resolveSlotAssetUrl(poster.brand_logo) || resolveSlotAssetUrl(stage1Data?.brand_logo) || '',
    scenarioSrc:
      resolveSlotAssetUrl(poster.scenario_image) ||
      resolveSlotAssetUrl(generation?.scenario_image) ||
      resolveSlotAssetUrl(stage1Data?.scenario_asset) ||
      '',
    productPrimarySrc:
      resolveSlotAssetUrl(poster.product_image) ||
      resolveSlotAssetUrl(generation?.product_image) ||
      resolveSlotAssetUrl(stage1Data?.product_asset || stage1Data?.product_image_1) ||
      '',
    productSecondarySrc: resolveSlotAssetUrl(stage1Data?.product_image_2) || '',
    galleryItems,
    bottomMode:
      generation?.bottom_contract_review?.effective_bottom_mode ||
      generation?.bottom_contract_review?.bottom_mode ||
      stage2State.poster2?.bottomContract?.bottomMode ||
      'title_gallery_split',
    galleryMode:
      generation?.bottom_contract_review?.gallery_mode ||
      stage2State.poster2?.bottomContract?.galleryMode ||
      'strip_local_visible_only',
    latestResult: generation || null,
  });
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

async function waitForImagesReady(container, timeoutMs = 4000) {
  if (!container) return true;
  const images = Array.from(container.querySelectorAll('img'));
  if (!images.length) return true;
  const pending = images.filter((img) => !(img.complete && img.naturalWidth > 0));
  if (!pending.length) return true;

  return new Promise((resolve) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      resolve(false);
    }, timeoutMs);
    let remaining = pending.length;
    const done = () => {
      if (settled) return;
      remaining -= 1;
      if (remaining <= 0) {
        settled = true;
        clearTimeout(timer);
        resolve(true);
      }
    };
    pending.forEach((img) => {
      img.addEventListener('load', done, { once: true });
      img.addEventListener('error', done, { once: true });
    });
  });
}

async function waitForFontsReady(timeoutMs = 3000) {
  if (!document.fonts || !document.fonts.ready) return true;
  return Promise.race([
    document.fonts.ready.then(() => true).catch(() => false),
    delay(timeoutMs).then(() => false),
  ]);
}

async function saveStage2Result(data) {
  if (!data) return;

  let previousKey = null;
  const existingRaw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (existingRaw) {
    try {
      const existing = JSON.parse(existingRaw);
      previousKey = existing?.final_poster?.storage_key || null;
    } catch (error) {
      console.warn('????????? 2 ???????????', error);
    }
  }

  const payload = { ...data };
  if (data.final_poster) {
    const key = data.final_poster.storage_key || createId();
    const source = getPosterImageSource(data.final_poster);
    if (source) {
      await assetStore.put(key, source);
    }
    payload.final_poster = {
      filename: data.final_poster.filename,
      media_type: data.final_poster.media_type,
      width: data.final_poster.width,
      height: data.final_poster.height,
      storage_key: key,
      url: data.final_poster.url || null,
      key: data.final_poster.key || null,
    };
    if (previousKey && previousKey != key) {
      await assetStore.delete(previousKey).catch(() => undefined);
    }
  }

  try {
    sessionStorage.setItem(STORAGE_KEYS.stage2, JSON.stringify(payload));
  } catch (error) {
    if (isQuotaError(error)) {
      console.warn('sessionStorage ????????????? 2 ???', error);
      try {
        sessionStorage.removeItem(STORAGE_KEYS.stage2);
        sessionStorage.setItem(STORAGE_KEYS.stage2, JSON.stringify(payload));
      } catch (innerError) {
        console.error('?????? 2 ??????????', innerError);
      }
    } else {
      console.error('???? 2 ?????', error);
    }
  }
}

async function loadStage2Result() {
  const raw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.final_poster?.storage_key) {
      const storedValue = await assetStore.get(parsed.final_poster.storage_key);
      if (storedValue) {
        applyStoredAssetValue(parsed.final_poster, storedValue);
      }
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
    const posterUrlInput = document.getElementById('stage3-poster-url');
    const posterKeyInput = document.getElementById('stage3-poster-key');
    const draftPreviewText = document.getElementById('email-preview-text');
    const draftSource = document.getElementById('email-draft-source');
    const emailRecipient = document.getElementById('email-recipient');
    const emailSubject = document.getElementById('email-subject');
    const emailText = document.getElementById('email-text');
    const emailHtml = document.getElementById('email-html');
    const emailHtmlPreview = document.getElementById('email-html-preview');
    const deliveryMode = document.getElementById('email-delivery-mode');
    const attachmentGroup = document.getElementById('email-attachment-group');
    const attachmentStatus = document.getElementById('email-attachment-status');
    const attachmentPosterPng = document.getElementById('attachment-poster-png');
    const attachmentPosterPdf = document.getElementById('attachment-poster-pdf');
    const sendButton = document.getElementById('send-email');
    const refreshButton = document.getElementById('refresh-email-preview');
    const acceptCopyButton = document.getElementById('accept-email-copy');
    const rejectCopyButton = document.getElementById('reject-email-copy');

    if (!sendButton || !refreshButton || !emailRecipient || !emailSubject || !emailText || !emailHtml) {
      return;
    }

    const stage2Result = await loadStage2Result();
    const posterKey = getPosterKeyFromLocation() || stage2Result?.poster_key || '';
    const apiCandidates = getApiCandidates(apiBaseInput?.value || null);
    let emailCopyDecision = 'pending';

    const setEmailCopyDecision = (decision, message) => {
      emailCopyDecision = decision;
      if (acceptCopyButton) acceptCopyButton.disabled = decision === 'accepted';
      if (rejectCopyButton) rejectCopyButton.disabled = decision === 'rejected';
      if (sendButton && decision !== 'rejected') sendButton.disabled = false;
      if (message) setStatus(statusElement, message, decision === 'rejected' ? 'warning' : 'info');
    };

    if (!posterKey) {
      setStatus(
        statusElement,
        '缺少 poster_key，无法从后端恢复 Stage 3 数据。',
        'warning'
      );
      sendButton.disabled = true;
      refreshButton.disabled = true;
      return;
    }

    async function hydratePosterRecord() {
      const record = await getJsonWithRetry(apiCandidates, `/api/v2/posters/${encodeURIComponent(posterKey)}`, 1);
      const finalPoster = record?.final_poster || stage2Result?.final_poster || null;
      if (!finalPoster) {
        throw new Error('poster_record missing final_poster');
      }
      assignPosterImage(
        posterImage,
        finalPoster,
        record?.request_snapshot?.title || 'Final poster'
      );
      if (posterCaption) {
        const captionParts = [
          record?.request_snapshot?.brand_name,
          record?.request_snapshot?.title,
        ].filter(Boolean);
        posterCaption.textContent = captionParts.join(' / ');
      }
      if (posterUrlInput) {
        posterUrlInput.value = finalPoster.url || '';
      }
      if (posterKeyInput) {
        posterKeyInput.value = record?.poster_key || posterKey;
      }
      if (!emailRecipient.value) {
        emailRecipient.value = DEFAULT_EMAIL_RECIPIENT;
      }
      return record;
    }

    async function refreshDraft() {
      setStatus(statusElement, '正在从 poster_record 生成邮件草稿…', 'info');
      const draft = await postJsonWithRetry(
        apiCandidates,
        '/api/v2/email/preview',
        { poster_key: posterKey },
        1
      );
      emailSubject.value = draft?.subject || '';
      if (draftPreviewText) {
        draftPreviewText.value = draft?.preview_text || '';
      }
      emailText.value = draft?.text || '';
      emailHtml.value = draft?.html || '';
      if (draftSource) {
        draftSource.textContent = `邮件文案来源：${draft?.generated_from || 'deterministic'} ｜ Tone: ${draft?.tone || 'clean_product_business'}`;
      }
      if (emailHtmlPreview) {
        emailHtmlPreview.innerHTML = draft?.html || '';
      }
      const availableAttachmentTypes = Array.isArray(draft?.available_attachment_types) ? draft.available_attachment_types : [];
      const buildableAttachmentTypes = Array.isArray(draft?.buildable_attachment_types) ? draft.buildable_attachment_types : [];
      const showAttachmentUi = availableAttachmentTypes.length > 0 || buildableAttachmentTypes.length > 0;
      if (attachmentGroup) {
        attachmentGroup.hidden = !showAttachmentUi;
      }
      if (attachmentPosterPng) {
        attachmentPosterPng.checked = availableAttachmentTypes.includes('poster_png');
        attachmentPosterPng.disabled = !availableAttachmentTypes.includes('poster_png');
      }
      if (attachmentPosterPdf) {
        attachmentPosterPdf.checked = availableAttachmentTypes.includes('poster_pdf');
        attachmentPosterPdf.disabled = !availableAttachmentTypes.includes('poster_pdf');
      }
      if (attachmentStatus) {
        attachmentStatus.textContent = showAttachmentUi
          ? `Available: ${availableAttachmentTypes.join(', ') || 'none'} | Buildable: ${buildableAttachmentTypes.join(', ') || 'none'}`
          : '暂无可选的后端附件。';
      }
      setStatus(statusElement, '邮件草稿已从后端恢复。', 'success');
      setEmailCopyDecision('pending');
      if (acceptCopyButton) acceptCopyButton.disabled = false;
      if (rejectCopyButton) rejectCopyButton.disabled = false;
      sendButton.disabled = false;
      return draft;
    }

    try {
      await warmUp(apiCandidates);
      await hydratePosterRecord();
      await refreshDraft();
    } catch (error) {
      console.error('[stage3 hydrate failed]', error);
      setStatus(statusElement, error.message || '环节 3 恢复失败。', 'error');
      sendButton.disabled = true;
      refreshButton.disabled = false;
      return;
    }

    emailHtml.addEventListener('input', () => {
      if (emailHtmlPreview) {
        emailHtmlPreview.innerHTML = emailHtml.value.trim();
      }
      setEmailCopyDecision('pending');
    });
    [emailSubject, draftPreviewText, emailText].forEach((input) => {
      input?.addEventListener('input', () => setEmailCopyDecision('pending'));
    });

    refreshButton.disabled = false;
    refreshButton.addEventListener('click', async () => {
      refreshButton.disabled = true;
      try {
        await refreshDraft();
      } catch (error) {
        console.error('[email preview]', error);
        setStatus(statusElement, error.message || '邮件预览生成失败。', 'error');
      } finally {
        refreshButton.disabled = false;
      }
    });

    if (acceptCopyButton) {
      acceptCopyButton.addEventListener('click', () => {
        setEmailCopyDecision('accepted', '本次发送已接受邮件文案。');
      });
    }

    if (rejectCopyButton) {
      rejectCopyButton.addEventListener('click', () => {
        setEmailCopyDecision('rejected', '已拒绝邮件文案；请 Refresh Draft 或手动编辑后再发送。');
        sendButton.disabled = true;
      });
    }

    sendButton.disabled = false;
    sendButton.addEventListener('click', async () => {
      const recipient = emailRecipient.value.trim();
      const subject = emailSubject.value.trim();
      const previewText = draftPreviewText?.value.trim() || '';
      const text = emailText.value.trim();
      const html = emailHtml.value.trim();
      const attachmentTypes = [
        attachmentPosterPng?.checked ? 'poster_png' : null,
        attachmentPosterPdf?.checked ? 'poster_pdf' : null,
      ].filter(Boolean);

      if (!recipient || !subject || !text || !html) {
        setStatus(statusElement, '请先完成收件人和邮件内容。', 'error');
        return;
      }
      if (emailCopyDecision === 'rejected') {
        setStatus(statusElement, '邮件文案已拒绝，请刷新或编辑后再发送。', 'error');
        return;
      }

      sendButton.disabled = true;
      setStatus(statusElement, '正在发送邮件…', 'info');

      try {
        const response = await postJsonWithRetry(
          apiCandidates,
          '/api/v2/email/send',
          {
            poster_key: posterKey,
            recipient,
            subject,
            preview_text: previewText,
            text,
            html,
            delivery_mode: deliveryMode?.value || 'inline_only',
            attachment_types: attachmentTypes,
          },
          1
        );

        if (response?.status === 'sent') {
          setStatus(statusElement, '邮件已发送。', 'success');
        } else if (response?.status === 'preview_only') {
          setStatus(statusElement, '邮件草稿已保存；当前为 inline_only，未外发。', 'warning');
        } else {
          setStatus(statusElement, response?.error || '邮件发送失败。', 'error');
        }
      } catch (error) {
        console.error('[email send]', error);
        setStatus(statusElement, error.message || '邮件发送失败。', 'error');
      } finally {
        sendButton.disabled = false;
      }
    });
  })();
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
  stage1Data.product_asset_extra_1 = await rehydrateStoredAsset(stage1Data.product_asset_extra_1);
  stage1Data.product_asset_extra_2 = await rehydrateStoredAsset(stage1Data.product_asset_extra_2);
  stage1Data.product_image_1 = await rehydrateStoredAsset(stage1Data.product_image_1);
  stage1Data.product_image_2 = await rehydrateStoredAsset(stage1Data.product_image_2);
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
