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
    templateSpec: null,
    galleryLimit: 4,
    galleryAllowsPrompt: true,
    galleryLabel: MATERIAL_DEFAULT_LABELS.gallery,
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
    const scenarioAllowsPrompt = scenarioMaterial.allowsPrompt !== false;
    const scenarioToggleLabel = form.querySelector('[data-material-toggle-label="scenario"]');
    if (scenarioToggleLabel) {
      scenarioToggleLabel.textContent = `${scenarioLabel}素材来源`;
    }
    const scenarioPromptOption = form.querySelector('[data-mode-option="scenario-prompt"]');
    if (scenarioPromptOption) {
      scenarioPromptOption.classList.toggle('hidden', !scenarioAllowsPrompt);
    }
    const scenarioFileLabel = form.querySelector('[data-material-label="scenario"]');
    if (scenarioFileLabel) {
      scenarioFileLabel.textContent = `${scenarioLabel}上传`;
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
    if (!scenarioAllowsPrompt && state.scenarioMode === 'prompt') {
      state.scenarioMode = 'upload';
      const uploadRadio = form.querySelector('input[name="scenario_mode"][value="upload"]');
      if (uploadRadio) {
        uploadRadio.checked = true;
      }
      const promptRadio = form.querySelector('input[name="scenario_mode"][value="prompt"]');
      if (promptRadio) {
        promptRadio.checked = false;
      }
    }
    applyModeToInputs('scenario', state, form, inlinePreviews, { initial: true });

    const productMaterial = materials.product || {};
    const productLabel = getMaterialLabel('product', productMaterial);
    const productAllowsPrompt = productMaterial.allowsPrompt !== false;
    const productToggleLabel = form.querySelector('[data-material-toggle-label="product"]');
    if (productToggleLabel) {
      productToggleLabel.textContent = `${productLabel}素材来源`;
    }
    const productPromptOption = form.querySelector('[data-mode-option="product-prompt"]');
    if (productPromptOption) {
      productPromptOption.classList.toggle('hidden', !productAllowsPrompt);
    }
    const productFileLabel = form.querySelector('[data-material-label="product"]');
    if (productFileLabel) {
      productFileLabel.textContent = `${productLabel}上传`;
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
    if (!productAllowsPrompt && state.productMode === 'prompt') {
      state.productMode = 'upload';
      const uploadRadio = form.querySelector('input[name="product_mode"][value="upload"]');
      if (uploadRadio) {
        uploadRadio.checked = true;
      }
      const promptRadio = form.querySelector('input[name="product_mode"][value="prompt"]');
      if (promptRadio) {
        promptRadio.checked = false;
      }
    }
    applyModeToInputs('product', state, form, inlinePreviews, { initial: true });

    const galleryMaterial = materials.gallery || {};
    const galleryLabel = getMaterialLabel('gallery', galleryMaterial);
    const galleryAllowsPrompt = galleryMaterial.allowsPrompt !== false;
    const slotCount = Array.isArray(spec?.gallery?.items)
      ? spec.gallery.items.length
      : null;
    const configuredCount = Number(galleryMaterial.count);
    const galleryLimit = Number.isFinite(configuredCount) && configuredCount > 0
      ? configuredCount
      : slotCount || state.galleryLimit || 4;
    state.galleryLabel = galleryLabel;
    state.galleryAllowsPrompt = galleryAllowsPrompt;
    if (state.galleryLimit !== galleryLimit) {
      const removed = state.galleryEntries.splice(galleryLimit);
      await Promise.all(
        removed.map((entry) => deleteStoredAsset(entry.asset))
      );
      state.galleryLimit = galleryLimit;
    } else {
      state.galleryLimit = galleryLimit;
    }
    if (!galleryAllowsPrompt) {
      state.galleryEntries.forEach((entry) => {
        if (entry.mode === 'prompt') {
          entry.mode = 'upload';
          entry.prompt = '';
        }
      });
    }

    const galleryLabelElement = document.querySelector('[data-gallery-label]');
    if (galleryLabelElement) {
      galleryLabelElement.textContent = `${galleryLabel}（${galleryLimit} 项，支持多选）`;
    }
    const galleryDescription = document.querySelector('[data-gallery-description]');
    if (galleryDescription) {
      galleryDescription.textContent = galleryAllowsPrompt
        ? `每个条目由一张图像与系列说明组成，可上传或使用 AI 生成，共需 ${galleryLimit} 项。`
        : `请上传 ${galleryLimit} 张${galleryLabel}并填写对应说明。`;
    }
    const galleryUploadButton = document.querySelector('[data-gallery-upload]');
    if (galleryUploadButton) {
      galleryUploadButton.textContent = `上传${galleryLabel}`;
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
      promptPlaceholder:
        galleryMaterial.promptPlaceholder || '描述要生成的小图内容',
    });
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
    refreshPreview
  );
  attachSingleImageHandler(
    form.querySelector('input[name="scenario_asset"]'),
    'scenario',
    inlinePreviews.scenario_asset,
    state,
    refreshPreview
  );
  attachSingleImageHandler(
    form.querySelector('input[name="product_asset"]'),
    'product',
    inlinePreviews.product_asset,
    state,
    refreshPreview
  );

  renderGalleryItems(state, galleryItemsContainer, {
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement,
    onChange: refreshPreview,
    allowPrompt: state.galleryAllowsPrompt,
    promptPlaceholder:
      state.templateSpec?.materials?.gallery?.promptPlaceholder ||
      '描述要生成的小图内容',
  });

  refreshPreview();

  if (galleryButton && galleryFileInput) {
    galleryButton.addEventListener('click', () => {
      galleryFileInput.click();
    });

    galleryFileInput.addEventListener('change', async (event) => {
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
          const dataUrl = await fileToDataUrl(file);
          const asset = await buildAsset(file, dataUrl, null);
          state.galleryEntries.push({
            id: createId(),
            caption: '',
            asset,
            mode: 'upload',
            prompt: '',
          });
        } catch (error) {
          console.error(error);
          setStatus(statusElement, '读取底部产品小图时发生错误。', 'error');
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

function attachSingleImageHandler(input, key, inlinePreview, state, refreshPreview) {
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
      const dataUrl = await fileToDataUrl(file);
      state[key] = await buildAsset(file, dataUrl, state[key]);
      if (inlinePreview) {
        inlinePreview.src = dataUrl;
      }
      state.previewBuilt = false;
      refreshPreview();
    } catch (error) {
      console.error(error);
    }
  });
}

function applyModeToInputs(target, state, form, inlinePreviews, options = {}) {
  const { initial = false } = options;
  const mode = target === 'scenario' ? state.scenarioMode : state.productMode;
  const fileInput = form.querySelector(`input[name="${target}_asset"]`);
  if (fileInput) {
    fileInput.disabled = mode === 'prompt';
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
    promptPlaceholder = '描述要生成的小图内容',
  } = options;
  if (!container) return;
  container.innerHTML = '';

  const limit = state.galleryLimit || 4;
  const label = state.galleryLabel || MATERIAL_DEFAULT_LABELS.gallery;

  state.galleryEntries.slice(0, limit).forEach((entry, index) => {
    entry.mode = entry.mode || 'upload';
    entry.prompt = typeof entry.prompt === 'string' ? entry.prompt : '';

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
    const modeLabel = document.createElement('span');
    modeLabel.textContent = '素材来源';
    modeToggle.appendChild(modeLabel);

    const radioName = `gallery_mode_${entry.id}`;
    const uploadLabel = document.createElement('label');
    const uploadRadio = document.createElement('input');
    uploadRadio.type = 'radio';
    uploadRadio.name = radioName;
    uploadRadio.value = 'upload';
    uploadLabel.appendChild(uploadRadio);
    uploadLabel.append(' 上传图像');

    modeToggle.appendChild(uploadLabel);

    let promptLabel;
    let promptRadio;
    if (allowPrompt) {
      promptLabel = document.createElement('label');
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
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      try {
        const dataUrl = await fileToDataUrl(file);
        entry.asset = await buildAsset(file, dataUrl, entry.asset);
        previewImage.src = dataUrl;
        state.previewBuilt = false;
        onChange?.();
      } catch (error) {
        console.error(error);
        setStatus(statusElement, '读取底部产品小图时发生错误。', 'error');
      }
    });
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
      if (!allowPrompt) {
        mode = 'upload';
      }
      entry.mode = mode;
      const isPrompt = mode === 'prompt';
      fileInput.disabled = isPrompt;
      promptTextarea.disabled = !isPrompt || !allowPrompt;
      if (isPrompt) {
        fileField.classList.add('mode-hidden');
        promptField.classList.add('mode-visible');
        if (!initial) {
          await deleteStoredAsset(entry.asset);
          entry.asset = null;
          previewImage.src = placeholder;
        } else if (!entry.asset?.dataUrl) {
          previewImage.src = placeholder;
        }
      } else {
        fileField.classList.remove('mode-hidden');
        promptField.classList.remove('mode-visible');
        previewImage.src = entry.asset?.dataUrl || placeholder;
      }
      if (!initial) {
        state.previewBuilt = false;
        onChange?.();
      }
    }

    uploadRadio.addEventListener('change', () => {
      if (uploadRadio.checked) {
        void applyGalleryMode('upload');
      }
    });
    if (allowPrompt && promptRadio) {
      promptRadio.addEventListener('change', () => {
        if (promptRadio.checked) {
          void applyGalleryMode('prompt');
        }
      });
    }

    if (!allowPrompt) {
      promptField.classList.add('hidden');
      promptTextarea.disabled = true;
      if (promptRadio) {
        promptRadio.disabled = true;
      }
      uploadRadio.checked = true;
      entry.mode = 'upload';
    } else {
      uploadRadio.checked = entry.mode !== 'prompt';
      if (promptRadio) {
        promptRadio.checked = entry.mode === 'prompt';
      }
    }

    promptTextarea.disabled = entry.mode !== 'prompt' || !allowPrompt;
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
  const scenarioLine = payload.scenario_mode === 'prompt'
    ? `AI 生成（描述：${payload.scenario_prompt || payload.scenario_image || '待补充'}）`
    : payload.scenario_asset
    ? `已上传应用场景图（描述：${payload.scenario_image || '待补充'}）`
    : payload.scenario_image || '应用场景描述待补充';
  const productLine = payload.product_mode === 'prompt'
    ? `AI 生成（${payload.product_prompt || payload.product_name || '描述待补充'}）`
    : payload.product_asset
    ? `已上传 45° 渲染图（${payload.product_name || '主产品'}）`
    : payload.product_name || '主产品名称待补充';
  const galleryLabel = payload.gallery_label || MATERIAL_DEFAULT_LABELS.gallery;
  const galleryLimit = payload.gallery_limit || 4;

  const featuresPreview = (payload.features.length ? payload.features : DEFAULT_STAGE1.features)
    .map((feature, index) => `    - 功能点${index + 1}: ${feature}`)
    .join('\n');

  const galleryEntries = Array.isArray(payload.gallery_entries)
    ? payload.gallery_entries.filter((entry) =>
        entry.mode === 'prompt' ? Boolean(entry.prompt) : Boolean(entry.asset)
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
    const promptGroup = document.getElementById('prompt-group');
    const emailGroup = document.getElementById('email-group');
    const promptTextarea = document.getElementById('glibatree-prompt');
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
        if (templateDescription) {
          templateDescription.textContent = assets.entry?.description || '';
        }
        const previewAssets = await prepareTemplatePreviewAssets(stage1Data);
        drawTemplatePreview(templateCanvas, assets, stage1Data, previewAssets);
      } catch (error) {
        console.error(error);
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
      triggerGeneration({
        stage1Data,
        statusElement,
        layoutStructure,
        posterOutput,
        aiPreview,
        aiSpinner,
        aiPreviewMessage,
        posterVisual,
        posterImage,
        promptGroup,
        emailGroup,
        promptTextarea,
        emailTextarea,
        generateButton,
        regenerateButton,
        nextButton,
      }).catch((error) => console.error(error));
    });

    if (regenerateButton) {
      regenerateButton.addEventListener('click', () => {
        triggerGeneration({
          stage1Data,
          statusElement,
          layoutStructure,
          posterOutput,
          aiPreview,
          aiSpinner,
          aiPreviewMessage,
          posterVisual,
          posterImage,
          promptGroup,
          emailGroup,
          promptTextarea,
          emailTextarea,
          generateButton,
          regenerateButton,
          nextButton,
        }).catch((error) => console.error(error));
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
    promptGroup,
    emailGroup,
    promptTextarea,
    emailTextarea,
    generateButton,
    regenerateButton,
    nextButton,
  } = options;

  const apiBase = (apiBaseInput?.value || '').trim();
  if (!apiBase) {
    setStatus(statusElement, '请先填写后端 API 地址。', 'warning');
    return null;
  }

  await hydrateStage1DataAssets(stage1Data);

  const templateId = stage1Data.template_id || DEFAULT_STAGE1.template_id;

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
    scenario_asset: stage1Data.scenario_asset?.dataUrl || null,
    product_asset: stage1Data.product_asset?.dataUrl || null,
    scenario_mode: stage1Data.scenario_mode || 'upload',
    scenario_prompt:
      stage1Data.scenario_mode === 'prompt'
        ? stage1Data.scenario_prompt || stage1Data.scenario_image
        : null,
    product_mode: stage1Data.product_mode || 'upload',
    product_prompt: stage1Data.product_prompt || null,
    gallery_items:
      stage1Data.gallery_entries?.map((entry) => ({
        caption: entry.caption?.trim() || null,
        asset: entry.asset?.dataUrl || null,
        mode: entry.mode || 'upload',
        prompt: entry.prompt?.trim() || null,
      })) || [],
  };

  generateButton.disabled = true;
  if (regenerateButton) {
    regenerateButton.disabled = true;
  }
  setStatus(statusElement, '正在生成海报与营销文案…', 'info');

  if (posterOutput) posterOutput.classList.remove('hidden');
  if (aiPreview) aiPreview.classList.remove('complete');
  if (aiSpinner) aiSpinner.classList.remove('hidden');
  if (aiPreviewMessage) aiPreviewMessage.textContent = 'Glibatree Art Designer 正在绘制海报…';
  if (posterVisual) posterVisual.classList.add('hidden');
  if (promptGroup) promptGroup.classList.add('hidden');
  if (emailGroup) emailGroup.classList.add('hidden');
  if (nextButton) nextButton.disabled = true;

  try {
    const response = await fetch(`${apiBase.replace(/\/$/, '')}/api/generate-poster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || '生成海报时发生错误。');
    }

    const data = await response.json();
    if (layoutStructure && data.layout_preview) {
      layoutStructure.textContent = data.layout_preview;
    }
    if (posterImage && data.poster_image?.data_url) {
      posterImage.src = data.poster_image.data_url;
      posterImage.alt = `${payload.product_name} 海报预览`;
    }
    if (promptTextarea) {
      promptTextarea.value = data.prompt || '';
    }
    if (emailTextarea) {
      emailTextarea.value = data.email_body || '';
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
      prompt: data.prompt,
      email_body: data.email_body,
      template_id: payload.template_id,
    };
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
    templateRegistryPromise = fetch(TEMPLATE_REGISTRY_PATH)
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
    fetch(`templates/${entry.spec}`).then((response) => {
      if (!response.ok) throw new Error('无法加载模板规范');
      return response.json();
    }),
    loadImageAsset(`templates/${entry.preview}`),
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
  const existingRaw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (existingRaw) {
    try {
      const existing = JSON.parse(existingRaw);
      previousKey = existing?.poster_image?.storage_key || null;
    } catch (error) {
      console.warn('无法解析现有的环节 2 数据，跳过旧键清理。', error);
    }
  }

  const payload = { ...data };
  if (data.poster_image) {
    const key = data.poster_image.storage_key || createId();
    if (data.poster_image.data_url) {
      await assetStore.put(key, data.poster_image.data_url);
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
      const dataUrl = await assetStore.get(parsed.poster_image.storage_key);
      if (dataUrl) {
        parsed.poster_image.data_url = dataUrl;
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

    if (posterImage && stage2Result.poster_image?.data_url) {
      posterImage.src = stage2Result.poster_image.data_url;
      posterImage.alt = `${stage1Data.product_name} 海报预览`;
    }
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
      const apiBase = (apiBaseInput?.value || '').trim();
      if (!apiBase) {
        setStatus(statusElement, '请先填写后端 API 地址。', 'warning');
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
      const response = await fetch(`${apiBase.replace(/\/$/, '')}/api/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient,
          subject,
          body,
          attachment: stage2Result.poster_image,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || '发送邮件时发生错误。');
      }

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

async function buildAsset(file, dataUrl, previousAsset) {
  const key = createId();
  await assetStore.put(key, dataUrl);
  if (previousAsset?.key && previousAsset.key !== key) {
    await assetStore.delete(previousAsset.key).catch(() => undefined);
  }
  return {
    key,
    dataUrl,
    name: file.name,
    type: file.type,
    size: typeof file.size === 'number' ? file.size : undefined,
    lastModified: file.lastModified ?? Date.now(),
  };
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function serialiseAssetForStorage(asset) {
  if (!asset || !asset.key) return null;
  const { key, name, type, size, lastModified } = asset;
  return {
    key,
    name: name || null,
    type: type || null,
    size: typeof size === 'number' ? size : null,
    lastModified: typeof lastModified === 'number' ? lastModified : null,
  };
}

async function rehydrateStoredAsset(assetMeta) {
  if (!assetMeta) return null;
  if (assetMeta.dataUrl) return assetMeta;
  if (!assetMeta.key) return null;
  const dataUrl = await assetStore.get(assetMeta.key);
  if (!dataUrl) return { ...assetMeta, dataUrl: null };
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
