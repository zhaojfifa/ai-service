const form = document.getElementById('poster-form');
const layoutStructure = document.getElementById('layout-structure-text');
const generateButton = document.getElementById('generate-poster');
const posterOutput = document.getElementById('poster-output');
const posterImage = document.getElementById('poster-image');
const glibatreePrompt = document.getElementById('glibatree-prompt');
const generatedEmail = document.getElementById('generated-email');
const emailRecipient = document.getElementById('email-recipient');
const emailSubject = document.getElementById('email-subject');
const emailBody = document.getElementById('email-body');
const sendButton = document.getElementById('send-email');
const statusElement = document.getElementById('status');
const apiBaseInput = document.getElementById('api-base');

const brandLogoInput = form.querySelector('input[name="brand_logo"]');
const scenarioAssetInput = form.querySelector('input[name="scenario_asset"]');
const productAssetInput = form.querySelector('input[name="product_asset"]');
const galleryAssetsInput = form.querySelector('input[name="gallery_assets"]');

const previewBrandLogo = document.getElementById('preview-brand-logo');
const previewBrandName = document.getElementById('preview-brand-name');
const previewAgentName = document.getElementById('preview-agent-name');
const previewScenarioImage = document.getElementById('preview-scenario-image');
const previewProductImage = document.getElementById('preview-product-image');
const previewFeatureList = document.getElementById('preview-feature-list');
const previewTitle = document.getElementById('preview-title');
const previewSubtitle = document.getElementById('preview-subtitle');
const previewGallery = document.getElementById('preview-gallery');
const previewSeries = document.getElementById('preview-series-description');

const STORAGE_KEY = 'marketing-poster-api-base';
let latestPosterImage = null;

const defaultData = {
  brand_name: '厨匠ChefCraft',
  agent_name: '味觉星球营销中心',
  scenario_image: '现代开放式厨房中智能蒸烤一体机的使用场景',
  product_name: 'ChefCraft 智能蒸烤大师',
  features: [
    '一键蒸烤联动，精准锁鲜',
    '360° 智能热风循环，均匀受热',
    '高温自清洁腔体，省心维护',
    'Wi-Fi 远程操控，云端菜谱推送',
  ],
  title: '焕新厨房效率，打造大厨级美味',
  series_description: '标准款 / 高配款 / 嵌入式款 产品三视图',
  subtitle: '智能蒸烤 · 家宴轻松掌控',
  email: 'client@example.com',
};

const placeholderImages = {
  brandLogo: createPlaceholder('品牌\\nLogo'),
  scenario: createPlaceholder('应用场景'),
  product: createPlaceholder('产品渲染'),
};

const placeholderGallery = Array.from({ length: 4 }, (_, index) =>
  createPlaceholder(`产品小图 ${index + 1}`)
);

const imageState = {
  brandLogo: null,
  scenario: null,
  product: null,
  gallery: [],
};

function createPlaceholder(text) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360">\n    <defs>\n      <style>\n        .bg { fill: #e5e9f0; }\n        .border { fill: none; stroke: #cbd2d9; stroke-width: 4; stroke-dasharray: 12 10; }\n        .label {\n          font-size: 28px;\n          font-family: 'Segoe UI', 'Noto Sans', sans-serif;\n          font-weight: 600;\n          fill: #3d4852;\n        }\n      </style>\n    </defs>\n    <rect class="bg" x="0" y="0" width="480" height="360" rx="32" />\n    <rect class="border" x="18" y="18" width="444" height="324" rx="26" />\n    <text class="label" x="50%" y="50%" dominant-baseline="middle" text-anchor="middle">${text}</text>\n  </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result?.toString() || '');
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
}

function normaliseAsset(value) {
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function getDisplaySource(value, fallback) {
  return value && value.length > 0 ? value : fallback;
}

function setStatus(message, level = 'info') {
  statusElement.textContent = message;
  statusElement.className = level ? `status-${level}` : '';
}

function loadApiBase() {
  const stored = localStorage.getItem(STORAGE_KEY) || '';
  if (stored) {
    apiBaseInput.value = stored;
  }
}

function saveApiBase() {
  if (apiBaseInput.value.trim()) {
    localStorage.setItem(STORAGE_KEY, apiBaseInput.value.trim());
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function applyDefaults() {
  for (const [key, value] of Object.entries(defaultData)) {
    if (key === 'features') continue;
    const element = form.elements.namedItem(key);
    if (element) {
      element.value = value;
    }
  }

  const featureInputs = form.querySelectorAll('input[name="features"]');
  featureInputs.forEach((input, index) => {
    input.value = defaultData.features[index] ?? '';
  });

  if (brandLogoInput) brandLogoInput.value = '';
  if (scenarioAssetInput) scenarioAssetInput.value = '';
  if (productAssetInput) productAssetInput.value = '';
  if (galleryAssetsInput) galleryAssetsInput.value = '';

  imageState.brandLogo = null;
  imageState.scenario = null;
  imageState.product = null;
  imageState.gallery = [];

  syncEmailFields(defaultData);
}

function syncEmailFields(data, emailText) {
  emailRecipient.value = data.email;
  emailSubject.value = `${data.brand_name} ${data.product_name} 市场推广海报`;
  if (emailText) {
    emailBody.value = emailText;
  }
}

function buildLayoutPreview(data) {
  const featuresPreview = data.features
    .map((feature, index) => `    - 功能点${index + 1}: ${feature}`)
    .join('\n');

  const logoLine = data.brand_logo
    ? `已上传品牌 Logo（${data.brand_name}）`
    : data.brand_name;
  const scenarioLine = data.scenario_asset
    ? `已上传场景图（描述：${data.scenario_image || '未填写'}）`
    : data.scenario_image || '待提供场景描述';
  const productLine = data.product_asset
    ? `已上传 45° 渲染图（${data.product_name}）`
    : data.product_name;
  const galleryLine = (data.gallery_assets?.length || 0) > 0
    ? `已上传 ${data.gallery_assets.length} 张底部产品小图，配文：${data.series_description}`
    : data.series_description;

  return `顶部横条\n  · 品牌 Logo（左上）：${logoLine}\n  · 代理 / 分销（右上）：${data.agent_name}\n\n左侧区域（约 40% 宽）\n  · 应用场景图：${scenarioLine}\n\n右侧区域（视觉中心）\n  · 主产品 45° 渲染图：${productLine}\n  · 功能点标注：\n${featuresPreview}\n\n中部标题（大号粗体红字）\n  · ${data.title}\n\n底部区域（三视图或系列说明）\n  · ${galleryLine}\n\n角落副标题 / 标语（大号粗体红字）\n  · ${data.subtitle}\n\n主色建议：黑（功能）、红（标题 / 副标题）、灰 / 银（金属质感）\n背景：浅灰或白色，整体保持现代、简洁与留白感。`;
}

function collectFormData({ strict } = { strict: false }) {
  const formData = new FormData(form);
  const payload = {
    brand_name: formData.get('brand_name')?.toString().trim() || '',
    agent_name: formData.get('agent_name')?.toString().trim() || '',
    scenario_image: formData.get('scenario_image')?.toString().trim() || '',
    product_name: formData.get('product_name')?.toString().trim() || '',
    features: formData
      .getAll('features')
      .map((feature) => feature.toString().trim())
      .filter((feature) => feature.length > 0),
    title: formData.get('title')?.toString().trim() || '',
    series_description: formData.get('series_description')?.toString().trim() || '',
    subtitle: formData.get('subtitle')?.toString().trim() || '',
    email: formData.get('email')?.toString().trim() || '',
  };

  payload.brand_logo = normaliseAsset(imageState.brandLogo);
  payload.scenario_asset = normaliseAsset(imageState.scenario);
  payload.product_asset = normaliseAsset(imageState.product);
  payload.gallery_assets = imageState.gallery.slice(0, 4).filter((asset) => !!asset);

  if (strict) {
    if (payload.features.length < 3 || payload.features.length > 4) {
      throw new Error('请填写 3-4 条产品功能点。');
    }
    for (const [key, value] of Object.entries(payload)) {
      if (key === 'features') continue;
      if (key.endsWith('_asset') || key === 'gallery_assets' || key === 'brand_logo') {
        continue;
      }
      if (!value) {
        throw new Error('请完整填写所有素材字段。');
      }
    }
  }

  return payload;
}

function updatePreview() {
  const data = collectFormData({ strict: false });
  const featuresForPreview = data.features.length ? data.features : defaultData.features;
  const layoutData = { ...data, features: featuresForPreview };

  if (layoutStructure) {
    layoutStructure.textContent = buildLayoutPreview(layoutData);
  }

  previewBrandLogo.src = getDisplaySource(imageState.brandLogo, placeholderImages.brandLogo);
  previewBrandName.textContent = data.brand_name || '品牌名称';
  previewAgentName.textContent = data.agent_name || '代理 / 分销名称';

  previewScenarioImage.src = getDisplaySource(imageState.scenario, placeholderImages.scenario);
  previewScenarioImage.alt = data.scenario_image
    ? `${data.scenario_image} - 场景预览`
    : '应用场景预览';

  previewProductImage.src = getDisplaySource(imageState.product, placeholderImages.product);
  previewProductImage.alt = data.product_name
    ? `${data.product_name} 渲染预览`
    : '产品渲染图预览';

  previewFeatureList.innerHTML = '';
  featuresForPreview.slice(0, 4).forEach((feature, index) => {
    const item = document.createElement('li');
    item.classList.add(`feature-tag-${index + 1}`);
    item.textContent = feature || `功能点 ${index + 1}`;
    previewFeatureList.appendChild(item);
  });

  previewTitle.textContent = data.title || '标题文案';
  previewSubtitle.textContent = data.subtitle || '副标题文案';

  const gallerySourcesBase = imageState.gallery.slice(0, 4);
  const gallerySources = gallerySourcesBase.length >= 3
    ? gallerySourcesBase
    : [...gallerySourcesBase, ...placeholderGallery].slice(0, 4);

  previewGallery.innerHTML = '';
  gallerySources.forEach((src, index) => {
    const img = document.createElement('img');
    img.src = src;
    img.alt = `产品小图 ${index + 1}`;
    previewGallery.appendChild(img);
  });

  previewSeries.textContent = data.series_description || defaultData.series_description;
}

async function handleSingleImageInput(input, key) {
  const file = input.files && input.files[0];
  if (!file) {
    imageState[key] = null;
    updatePreview();
    return;
  }

  try {
    imageState[key] = await fileToDataUrl(file);
  } catch (error) {
    console.error(error);
    imageState[key] = null;
    setStatus('无法读取上传的图片，请重试。', 'error');
  }
  updatePreview();
}

async function handleGalleryInput(input) {
  const files = input.files ? Array.from(input.files).slice(0, 4) : [];
  if (!files.length) {
    imageState.gallery = [];
    updatePreview();
    return;
  }

  try {
    const assets = await Promise.all(files.map((file) => fileToDataUrl(file)));
    imageState.gallery = assets;
  } catch (error) {
    console.error(error);
    imageState.gallery = [];
    setStatus('无法读取底部产品小图，请重试。', 'error');
  }
  updatePreview();
}

async function generatePoster() {
  const apiBase = (apiBaseInput.value || '').trim();
  if (!apiBase) {
    setStatus('请先填写后端 API 地址。', 'warning');
    return;
  }

  let payload;
  try {
    payload = collectFormData({ strict: true });
  } catch (error) {
    setStatus(error.message, 'error');
    return;
  }

  setStatus('正在生成海报与邮件草稿...', 'info');
  generateButton.disabled = true;

  try {
    const response = await fetch(`${apiBase.replace(/\/$/, '')}/api/generate-poster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`生成失败：${errorText}`);
    }

    const data = await response.json();
    if (layoutStructure) {
      layoutStructure.textContent = data.layout_preview;
    }
    glibatreePrompt.value = data.prompt;
    generatedEmail.value = data.email_body;
    emailBody.value = data.email_body;
    syncEmailFields(payload, data.email_body);

    posterImage.src = data.poster_image.data_url;
    posterImage.alt = `${payload.product_name} 海报预览`;
    latestPosterImage = data.poster_image;
    posterOutput.classList.remove('hidden');

    setStatus('海报与文案生成完成，请确认后发送邮件。', 'success');
  } catch (error) {
    console.error(error);
    setStatus(error.message || '生成海报时发生错误。', 'error');
  } finally {
    generateButton.disabled = false;
  }
}

async function sendEmail() {
  const apiBase = (apiBaseInput.value || '').trim();
  if (!apiBase) {
    setStatus('请先填写后端 API 地址。', 'warning');
    return;
  }

  if (!latestPosterImage) {
    setStatus('请先完成海报生成步骤。', 'warning');
    return;
  }

  const recipient = emailRecipient.value.trim();
  const subject = emailSubject.value.trim();
  const body = emailBody.value.trim();

  if (!recipient || !subject || !body) {
    setStatus('请完整填写收件邮箱、主题与邮件正文。', 'error');
    return;
  }

  setStatus('正在发送营销邮件...', 'info');
  sendButton.disabled = true;

  try {
    const response = await fetch(`${apiBase.replace(/\/$/, '')}/api/send-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipient,
        subject,
        body,
        attachment: latestPosterImage,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`发送失败：${errorText}`);
    }

    const data = await response.json();
    if (data.status === 'sent') {
      setStatus('邮件已成功发送。', 'success');
    } else {
      setStatus(data.detail || '邮件服务未配置，未执行发送。', 'warning');
    }
  } catch (error) {
    console.error(error);
    setStatus(error.message || '发送邮件时发生错误。', 'error');
  } finally {
    sendButton.disabled = false;
  }
}

function attachImageListeners() {
  if (brandLogoInput) {
    brandLogoInput.addEventListener('change', () => {
      handleSingleImageInput(brandLogoInput, 'brandLogo');
    });
  }
  if (scenarioAssetInput) {
    scenarioAssetInput.addEventListener('change', () => {
      handleSingleImageInput(scenarioAssetInput, 'scenario');
    });
  }
  if (productAssetInput) {
    productAssetInput.addEventListener('change', () => {
      handleSingleImageInput(productAssetInput, 'product');
    });
  }
  if (galleryAssetsInput) {
    galleryAssetsInput.addEventListener('change', () => {
      handleGalleryInput(galleryAssetsInput);
    });
  }
}

apiBaseInput.addEventListener('change', () => {
  saveApiBase();
});

form.addEventListener('input', () => {
  updatePreview();
});

attachImageListeners();

generateButton.addEventListener('click', (event) => {
  event.preventDefault();
  generatePoster();
});

sendButton.addEventListener('click', (event) => {
  event.preventDefault();
  sendEmail();
});

(function init() {
  loadApiBase();
  applyDefaults();
  updatePreview();
  generatedEmail.setAttribute('readonly', 'readonly');
  setStatus('请确认素材内容，完成海报生成与邮件发送流程。', 'info');
})();
