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
  features: [
    '一键蒸烤联动，精准锁鲜',
    '360° 智能热风循环，均匀受热',
    '高温自清洁腔体，省心维护',
    'Wi-Fi 远程操控，云端菜谱推送',
  ],
  title: '焕新厨房效率，打造大厨级美味',
  subtitle: '智能蒸烤 · 家宴轻松掌控',
};

const DEFAULT_EMAIL_RECIPIENT = 'client@example.com';

const placeholderImages = {
  brandLogo: createPlaceholder('品牌\\nLogo'),
  scenario: createPlaceholder('应用场景'),
  product: createPlaceholder('产品渲染'),
  gallery: Array.from({ length: 4 }, (_, index) =>
    createPlaceholder(`底部小图 ${index + 1}`)
  ),
};

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
  const galleryFileInput = document.getElementById('gallery-file-input');
  const galleryItemsContainer = document.getElementById('gallery-items');

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
  };

  let currentLayoutPreview = '';
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
    applyStage1DataToForm(stored, form, state, inlinePreviews);
    state.previewBuilt = Boolean(stored.preview_built);
    currentLayoutPreview = stored.layout_preview || '';
  } else {
    applyStage1Defaults(form);
    updateInlinePlaceholders(inlinePreviews);
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
      const remaining = Math.max(0, 4 - state.galleryEntries.length);
      if (remaining <= 0) {
        setStatus(statusElement, '最多仅支持上传 4 张底部产品小图。', 'warning');
        galleryFileInput.value = '';
        return;
      }

      const selected = files.slice(0, remaining);
      for (const file of selected) {
        try {
          const dataUrl = await fileToDataUrl(file);
          state.galleryEntries.push({
            id: createId(),
            caption: '',
            asset: buildAsset(file, dataUrl),
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
}

function updateInlinePlaceholders(inlinePreviews) {
  if (inlinePreviews.brand_logo) inlinePreviews.brand_logo.src = placeholderImages.brandLogo;
  if (inlinePreviews.scenario_asset) inlinePreviews.scenario_asset.src = placeholderImages.scenario;
  if (inlinePreviews.product_asset) inlinePreviews.product_asset.src = placeholderImages.product;
}

function applyStage1DataToForm(data, form, state, inlinePreviews) {
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

  state.brandLogo = data.brand_logo || null;
  state.scenario = data.scenario_asset || null;
  state.product = data.product_asset || null;
  state.galleryEntries = Array.isArray(data.gallery_entries)
    ? data.gallery_entries.map((entry) => ({
        id: entry.id || createId(),
        caption: entry.caption || '',
        asset: entry.asset || null,
      }))
    : [];

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
      state[key] = buildAsset(file, dataUrl);
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
function renderGalleryItems(state, container, options = {}) {
  const {
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement,
    onChange,
  } = options;
  if (!container) return;
  container.innerHTML = '';

  state.galleryEntries.slice(0, 4).forEach((entry, index) => {
    const item = document.createElement('div');
    item.classList.add('gallery-item');
    item.dataset.id = entry.id;

    const header = document.createElement('div');
    header.classList.add('gallery-item-header');
    const title = document.createElement('span');
    title.classList.add('gallery-item-title');
    title.textContent = `底部产品 ${index + 1}`;
    header.appendChild(title);

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.classList.add('secondary');
    removeButton.textContent = '移除';
    removeButton.addEventListener('click', () => {
      state.galleryEntries = state.galleryEntries.filter((g) => g.id !== entry.id);
      state.previewBuilt = false;
      renderGalleryItems(state, container, {
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement,
        onChange,
      });
      onChange?.();
    });

    const actions = document.createElement('div');
    actions.classList.add('gallery-item-actions');
    actions.appendChild(removeButton);
    header.appendChild(actions);
    item.appendChild(header);

    const fileField = document.createElement('label');
    fileField.classList.add('field', 'file-field');
    fileField.innerHTML = '<span>上传产品小图</span>';
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      try {
        const dataUrl = await fileToDataUrl(file);
        entry.asset = buildAsset(file, dataUrl);
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
    previewImage.alt = `底部产品 ${index + 1} 预览`;
    previewImage.src = entry.asset?.dataUrl || placeholderImages.gallery[index];
    previewWrapper.appendChild(previewImage);
    item.appendChild(previewWrapper);

    const captionField = document.createElement('label');
    captionField.classList.add('field', 'gallery-caption');
    captionField.innerHTML = '<span>小图文案</span>';
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

  const galleryEntries = state.galleryEntries.map((entry) => ({
    id: entry.id,
    caption: entry.caption.trim(),
    asset: entry.asset,
  }));

  const validGalleryEntries = galleryEntries.filter((entry) => entry.asset);

  payload.series_description = validGalleryEntries.length
    ? validGalleryEntries
        .map((entry, index) => `小图${index + 1}：${entry.caption || '系列说明待补充'}`)
        .join(' / ')
    : '';

  payload.brand_logo = state.brandLogo;
  payload.scenario_asset = state.scenario;
  payload.product_asset = state.product;
  payload.gallery_entries = galleryEntries;

  if (strict) {
    const missing = [];
    for (const [key, value] of Object.entries(payload)) {
      if (['brand_logo', 'scenario_asset', 'product_asset', 'gallery_entries'].includes(key)) {
        continue;
      }
      if (typeof value === 'string' && !value) {
        missing.push(key);
      }
    }
    if (payload.features.length < 3) {
      throw new Error('请填写至少 3 条产品功能点。');
    }
    if (validGalleryEntries.length < 3) {
      throw new Error('请上传至少 3 张底部产品小图，并填写对应文案。');
    }
    const captionsIncomplete = validGalleryEntries.some((entry) => !entry.caption);
    if (captionsIncomplete) {
      throw new Error('请为每张底部产品小图填写文案说明。');
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
    const entries = state.galleryEntries.slice(0, 4);
    const placeholders = placeholderImages.gallery;
    const total = Math.max(entries.length, 3);
    for (let index = 0; index < total; index += 1) {
      const entry = entries[index];
      const figure = document.createElement('figure');
      const img = document.createElement('img');
      const caption = document.createElement('figcaption');
      if (entry?.asset?.dataUrl) {
        img.src = entry.asset.dataUrl;
      } else {
        img.src = placeholders[index] || placeholders[placeholders.length - 1];
      }
      img.alt = `底部产品 ${index + 1} 预览`;
      caption.textContent = entry?.caption || `底部小图 ${index + 1}`;
      figure.appendChild(img);
      figure.appendChild(caption);
      gallery.appendChild(figure);
    }
  }

  return layoutText;
}

function buildLayoutPreview(payload) {
  const logoLine = payload.brand_logo
    ? `已上传品牌 Logo（${payload.brand_name}）`
    : payload.brand_name || '品牌 Logo 待上传';
  const scenarioLine = payload.scenario_asset
    ? `已上传应用场景图（描述：${payload.scenario_image || '待补充'}）`
    : payload.scenario_image || '应用场景描述待补充';
  const productLine = payload.product_asset
    ? `已上传 45° 渲染图（${payload.product_name}）`
    : payload.product_name || '主产品名称待补充';

  const featuresPreview = (payload.features.length ? payload.features : DEFAULT_STAGE1.features)
    .map((feature, index) => `    - 功能点${index + 1}: ${feature}`)
    .join('\n');

  const galleryEntries = payload.gallery_entries?.filter((entry) => entry.asset) ?? [];
  const gallerySummary = galleryEntries.length
    ? galleryEntries
        .map((entry, index) => `    · 底部产品小图${index + 1}：${entry.caption || '系列说明待补充'}`)
        .join('\n')
    : '    · 底部产品小图待上传（需提供 3-4 张灰度素材并附文字说明）。';

  return `顶部横条\n  · 品牌 Logo（左上）：${logoLine}\n  · 品牌代理名 / 分销名（右上）：${
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
    brand_logo: state.brandLogo,
    scenario_asset: state.scenario,
    product_asset: state.product,
    gallery_entries: state.galleryEntries.map((entry) => ({
      id: entry.id,
      caption: entry.caption,
      asset: entry.asset,
    })),
    layout_preview: layoutPreview,
    preview_built: previewBuilt,
  };
}

function saveStage1Data(data) {
  sessionStorage.setItem(STORAGE_KEYS.stage1, JSON.stringify(data));
  sessionStorage.removeItem(STORAGE_KEYS.stage2);
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

  populateStage1Summary(stage1Data, overviewList);
  if (layoutStructure && stage1Data.layout_preview) {
    layoutStructure.textContent = stage1Data.layout_preview;
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

  nextButton.addEventListener('click', () => {
    const stored = loadStage2Result();
    if (!stored || !stored.poster_image) {
      setStatus(statusElement, '请先完成海报生成，再前往环节 3。', 'warning');
      return;
    }
    window.location.href = 'stage3.html';
  });
}

function populateStage1Summary(stage1Data, overviewList) {
  if (!overviewList) return;
  overviewList.innerHTML = '';

  const entries = [
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
      '底部产品',
      `${stage1Data.gallery_entries?.filter((entry) => entry.asset).length || 0} 张小图`,
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

  const payload = {
    brand_name: stage1Data.brand_name,
    agent_name: stage1Data.agent_name,
    scenario_image: stage1Data.scenario_image,
    product_name: stage1Data.product_name,
    features: stage1Data.features,
    title: stage1Data.title,
    subtitle: stage1Data.subtitle,
    series_description: stage1Data.series_description,
    brand_logo: stage1Data.brand_logo?.dataUrl || null,
    scenario_asset: stage1Data.scenario_asset?.dataUrl || null,
    product_asset: stage1Data.product_asset?.dataUrl || null,
    gallery_assets:
      stage1Data.gallery_entries
        ?.filter((entry) => entry.asset)
        .map((entry) => entry.asset?.dataUrl)
        .filter(Boolean) || [],
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
    };
    saveStage2Result(stage2Result);
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

function saveStage2Result(data) {
  sessionStorage.setItem(STORAGE_KEYS.stage2, JSON.stringify(data));
}

function loadStage2Result() {
  const raw = sessionStorage.getItem(STORAGE_KEYS.stage2);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (error) {
    console.error('Unable to parse stage2 result', error);
    return null;
  }
}
function initStage3() {
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
  const stage2Result = loadStage2Result();

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

function buildAsset(file, dataUrl) {
  return {
    dataUrl,
    name: file.name,
    type: file.type,
    lastModified: file.lastModified,
  };
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
