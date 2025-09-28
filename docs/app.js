/* app.js — multi-stage (stage1 / stage2 / stage3) */

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

/* ========== App bootstrap ========== */
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
  if (stored) apiBaseInput.value = stored;
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

/* ========== Stage 1 ========== */
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

  if (!form || !buildPreviewButton || !nextButton) return;

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

  const stored = loadStage1Data();
  if (stored) {
    applyStage1DataToForm(stored, form, state, inlinePreviews);
    currentLayoutPreview = stored.layout_preview || '';
    if (stored.preview_built && previewContainer) {
      const payload = collectStage1Data(form, state, { strict: false });
      currentLayoutPreview = buildLayoutPreview(payload);
      updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
      state.previewBuilt = true;
    }
  } else {
    applyStage1Defaults(form);
    updateInlinePlaceholders(inlinePreviews);
  }

  attachSingleImageHandler(
    form.querySelector('input[name="brand_logo"]'),
    'brandLogo',
    inlinePreviews.brand_logo,
    state,
    previewElements,
    layoutStructure,
    previewContainer
  );
  attachSingleImageHandler(
    form.querySelector('input[name="scenario_asset"]'),
    'scenario',
    inlinePreviews.scenario_asset,
    state,
    previewElements,
    layoutStructure,
    previewContainer
  );
  attachSingleImageHandler(
    form.querySelector('input[name="product_asset"]'),
    'product',
    inlinePreviews.product_asset,
    state,
    previewElements,
    layoutStructure,
    previewContainer
  );

  renderGalleryItems(
    state,
    galleryItemsContainer,
    previewElements,
    layoutStructure,
    previewContainer,
    statusElement
  );

  if (galleryButton && galleryFileInput) {
    galleryButton.addEventListener('click', () => {
      galleryFileInput.click();
    });

    galleryFileInput.addEventListener('change', async (event) => {
      const files = Array.from(event.target.files || []);
      if (!files.length) return;

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
      renderGalleryItems(
        state,
        galleryItemsContainer,
        previewElements,
        layoutStructure,
        previewContainer,
        statusElement
      );
      if (state.previewBuilt) {
        const payload = collectStage1Data(form, state, { strict: false });
        currentLayoutPreview = buildLayoutPreview(payload);
        updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
      }
    });
  }

  form.addEventListener('input', () => {
    if (!state.previewBuilt) return;
    const payload = collectStage1Data(form, state, { strict: false });
    currentLayoutPreview = buildLayoutPreview(payload);
    updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
  });

  buildPreviewButton.addEventListener('click', () => {
    try {
      const payload = collectStage1Data(form, state, { strict: true });
      currentLayoutPreview = buildLayoutPreview(payload);
      updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
      state.previewBuilt = true;
      const serialised = serialiseStage1Data(payload, state, currentLayoutPreview, true);
      saveStage1Data(serialised);
      setStatus(statusElement, '版式预览已构建，可继续下一环节。', 'success');
    } catch (error) {
      console.error(error);
      setStatus(statusElement, error.message || '构建版式预览失败，请检查输入。', 'error');
    }
  });

  nextButton.addEventListener('click', () => {
    try {
      const payload = collectStage1Data(form, state, { strict: true });
      currentLayoutPreview = buildLayoutPreview(payload);
      updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
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

function attachSingleImageHandler(input, key, inlinePreview, state, previewElements, layoutStructure, previewContainer) {
  if (!input) return;
  input.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) {
      state[key] = null;
      if (inlinePreview) {
        const placeholder =
          key === 'brandLogo'
            ? placeholderImages.brandLogo
            : key === 'scenario'
            ? placeholderImages.scenario
            : placeholderImages.product;
        inlinePreview.src = placeholder;
      }
      return;
    }
    try {
      const dataUrl = await fileToDataUrl(file);
      state[key] = buildAsset(file, dataUrl);
      if (inlinePreview) {
        inlinePreview.src = dataUrl;
      }
      const form = input.form;
      if (form && previewContainer?.classList.contains('hidden') === false) {
        const payload = collectStage1Data(form, state, { strict: false });
        updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
      }
    } catch (error) {
      console.error(error);
    }
  });
}

function renderGalleryItems(state, container, previewElements, layoutStructure, previewContainer, statusElement) {
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
      renderGalleryItems(state, container, previewElements, layoutStructure, previewContainer, statusElement);
      if (previewContainer?.classList.contains('hidden') === false) {
        const form = document.getElementById('poster-form');
        if (form) {
          const payload = collectStage1Data(form, state, { strict: false });
          updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
        }
      }
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
        if (previewContainer?.classList.contains('hidden') === false) {
          const form = document.getElementById('poster-form');
          if (form) {
            const payload = collectStage1Data(form, state, { strict: false });
            updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
          }
        }
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
      if (previewContainer?.classList.contains('hidden') === false) {
        const form = document.getElementById('poster-form');
        if (form) {
          const payload = collectStage1Data(form, state, { strict: false });
          updatePosterPreview(payload, state, previewElements, layoutStructure, previewContainer);
        }
      }
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
      if (['brand_logo', 'scenario_asset', 'product_asset', 'gallery_entries'].includes(key)) continue;
      if (typeof value === 'string' && !value) missing.push(key);
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

  if (layoutStructure) {
    layoutStructure.textContent = buildLayoutPreview(payload);
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

  const featuresPreview = (payload.features.length ? payload.features
