/*
 * Route A front-end for ai-service (GitHub Pages)
 * Stage 1: layout selection + content entry + slot image uploads
 * Stage 2: reuse same layout, optionally call backend to generate images/text
 * Shared state is stored in localStorage under ROUTE_A_DRAFT_KEY
 */

const ROUTE_A_DRAFT_KEY = 'routeA.posterDraft';
const API_BASE_KEY = 'routeA.apiBase';
const FALLBACK_IMAGE = 'https://example.com/placeholder.png';

const LAYOUTS = {
  'hero-left': {
    id: 'hero-left',
    name: '左侧大图',
    description: '主视觉在左侧，右侧文案与功能点，底部四图。',
    slots: ['brandLogo', 'heroImage', 'productImage', 'gallery1', 'gallery2', 'gallery3', 'gallery4'],
  },
  'hero-right': {
    id: 'hero-right',
    name: '右侧大图',
    description: '主视觉在右侧，左侧文案，底部四图。',
    slots: ['brandLogo', 'heroImage', 'productImage', 'gallery1', 'gallery2', 'gallery3', 'gallery4'],
  },
  'hero-top': {
    id: 'hero-top',
    name: '顶部大图',
    description: '主视觉在顶部，下方文案与四图。',
    slots: ['brandLogo', 'heroImage', 'productImage', 'gallery1', 'gallery2', 'gallery3', 'gallery4'],
  },
};

function getDefaultDraft() {
  return {
    layoutId: 'hero-left',
    texts: {
      brand: '',
      slogan: '',
      highlights: '',
      cta: '',
    },
    assets: {
      brandLogo: '',
      heroImage: '',
      productImage: '',
      gallery1: '',
      gallery2: '',
      gallery3: '',
      gallery4: '',
      posterUrl: '',
    },
    prompts: {
      brand: '',
      scenario: '',
      product: '',
      benefits: '',
    },
    layoutPreview: '',
  };
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(ROUTE_A_DRAFT_KEY);
    if (!raw) return getDefaultDraft();
    const parsed = JSON.parse(raw);
    const defaults = getDefaultDraft();
    return {
      ...defaults,
      ...parsed,
      texts: { ...defaults.texts, ...parsed.texts },
      assets: { ...defaults.assets, ...parsed.assets },
      prompts: { ...defaults.prompts, ...parsed.prompts },
      layoutPreview: parsed.layoutPreview || '',
    };
  } catch (e) {
    console.warn('failed to load draft', e);
    return getDefaultDraft();
  }
}

function saveDraft(draft) {
  localStorage.setItem(ROUTE_A_DRAFT_KEY, JSON.stringify(draft));
}

function getApiBase() {
  const input = document.getElementById('api-base');
  const stored = localStorage.getItem(API_BASE_KEY) || '';
  const current = (input && input.value.trim()) || stored;
  if (input && current !== input.value) input.value = current;
  return current;
}

function bindApiBaseInput() {
  const input = document.getElementById('api-base');
  if (!input) return;
  const stored = localStorage.getItem(API_BASE_KEY);
  if (stored && !input.value) input.value = stored;
  input.addEventListener('input', () => {
    localStorage.setItem(API_BASE_KEY, input.value.trim());
  });
}

async function postJson(apiBase, path, payload) {
  if (!apiBase) throw new Error('后端 API 地址未配置');
  const url = `${apiBase.replace(/\/$/, '')}${path}`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => '');
    throw new Error(`HTTP ${resp.status} ${resp.statusText} ${detail || ''}`.trim());
  }
  return resp.json();
}

async function uploadFileToR2(file, { folder = 'uploads' } = {}) {
  const apiBase = getApiBase();
  if (!apiBase) throw new Error('请先填写后端 API 地址，再上传图片。');
  const payload = {
    folder,
    filename: file.name || 'upload.bin',
    content_type: file.type || 'application/octet-stream',
    size: typeof file.size === 'number' ? file.size : null,
  };
  const presign = await postJson(apiBase, '/api/r2/presign-put', payload);
  if (!presign || !presign.put_url || !presign.key) {
    throw new Error('预签名上传接口返回异常');
  }
  const headers = { 'Content-Type': payload.content_type };
  const putRes = await fetch(presign.put_url, { method: 'PUT', headers, body: file, mode: 'cors' });
  if (!putRes.ok) {
    const txt = await putRes.text().catch(() => '');
    throw new Error(`R2 上传失败：HTTP ${putRes.status} ${txt}`.trim());
  }
  const publicUrl = presign.get_url || presign.public_url || null;
  return { key: presign.key, url: publicUrl || presign.r2_url || null };
}

function renderLayoutCards(container, currentId) {
  if (!container) return;
  container.innerHTML = '';
  Object.values(LAYOUTS).forEach((layout) => {
    const card = document.createElement('div');
    card.className = 'layout-card';
    card.dataset.layoutId = layout.id;
    if (layout.id === currentId) card.classList.add('is-selected');

    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'layout';
    radio.value = layout.id;
    radio.checked = layout.id === currentId;

    const title = document.createElement('h4');
    title.textContent = layout.name;

    const desc = document.createElement('p');
    desc.textContent = layout.description;

    card.appendChild(radio);
    card.appendChild(title);
    card.appendChild(desc);
    container.appendChild(card);
  });
}

function applyLayoutSelection(container, draft, onChange) {
  if (!container) return;
  container.addEventListener('change', (evt) => {
    const target = evt.target;
    if (target.name === 'layout') {
      draft.layoutId = target.value;
      renderLayoutCards(container, draft.layoutId);
      if (typeof onChange === 'function') onChange();
    }
  });
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderPosterPreview(container, draft) {
  if (!container) return;
  container.dataset.layoutId = draft.layoutId;
  container.querySelector('[data-slot="brand"]')?.textContent = draft.texts.brand || '';
  container.querySelector('[data-slot="slogan"]')?.textContent = draft.texts.slogan || '';
  container.querySelector('[data-slot="highlights"]')?.textContent = draft.texts.highlights || '';
  container.querySelector('[data-slot="cta"]')?.textContent = draft.texts.cta || '';

  const logoImg = container.querySelector('[data-slot="logo"]');
  if (logoImg) logoImg.src = draft.assets.brandLogo || FALLBACK_IMAGE;

  const heroImg = container.querySelector('[data-slot="hero"]');
  if (heroImg) heroImg.src = draft.assets.heroImage || draft.assets.brandLogo || FALLBACK_IMAGE;

  const productImg = container.querySelector('[data-slot="product"]');
  if (productImg) productImg.src = draft.assets.productImage || draft.assets.heroImage || FALLBACK_IMAGE;

  const gallerySlots = container.querySelectorAll('[data-slot^="gallery-"]');
  gallerySlots.forEach((img, idx) => {
    const key = `gallery${idx + 1}`;
    img.src = draft.assets[key] || draft.assets.brandLogo || FALLBACK_IMAGE;
  });
}

function attachTextListeners(draft, previewRoot) {
  const mapping = [
    ['input-brand-name', 'brand'],
    ['input-slogan', 'slogan'],
    ['input-product-highlights', 'highlights'],
    ['input-call-to-action', 'cta'],
  ];
  mapping.forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = draft.texts[key] || '';
    el.addEventListener('input', () => {
      draft.texts[key] = el.value;
      saveDraft(draft);
      renderPosterPreview(previewRoot, draft);
    });
  });
}

function attachPromptListeners(draft) {
  const fields = document.querySelectorAll('[data-prompt-slot]');
  fields.forEach((el) => {
    const slot = el.dataset.promptSlot;
    const type = el.dataset.promptType || 'text';
    el.value = draft.prompts[slot] || '';
    el.addEventListener('input', () => {
      draft.prompts[slot] = el.value;
      saveDraft(draft);
      renderPromptPreview(draft);
    });
  });
}

function attachFileListeners(draft, previewRoot) {
  const mapping = [
    ['upload-brand-logo', 'brandLogo'],
    ['upload-hero-image', 'heroImage'],
    ['upload-product-image', 'productImage'],
    ['upload-gallery-1', 'gallery1'],
    ['upload-gallery-2', 'gallery2'],
    ['upload-gallery-3', 'gallery3'],
    ['upload-gallery-4', 'gallery4'],
  ];
  mapping.forEach(([id, key]) => {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('change', async () => {
      const file = input.files?.[0];
      if (!file) return;
      const preview = document.querySelector(`[data-preview-for="${id}"]`);
      try {
        const dataUrl = await readFileAsDataUrl(file);
        if (preview) preview.src = dataUrl;
      } catch (e) {
        console.warn('预览文件失败', e);
      }
      try {
        const uploaded = await uploadFileToR2(file, { folder: 'slots' });
        if (uploaded?.url) {
          draft.assets[key] = uploaded.url;
          saveDraft(draft);
          renderPosterPreview(previewRoot, draft);
        }
      } catch (err) {
        console.error('上传失败', err);
        alert('上传图片失败，请检查后端或 CORS 设置');
      }
    });
  });
}

function renderPromptPreview(draft) {
  const templateEl = document.getElementById('template-default-prompt');
  if (templateEl) {
    templateEl.textContent = draft.prompts.brand || '模板默认英文提示词占位';
  }
  const summaryEl = document.getElementById('prompt-preview-text');
  if (!summaryEl) return;
  const lines = [];
  lines.push('品牌/代理：');
  lines.push(draft.prompts.brand || '（未填写）');
  lines.push('\n场景：');
  lines.push(draft.prompts.scenario || '（未填写）');
  lines.push('\n产品：');
  lines.push(draft.prompts.product || '（未填写）');
  lines.push('\n卖点/Benefits：');
  lines.push(draft.prompts.benefits || '（未填写）');
  summaryEl.textContent = lines.join('\n');
}

function buildPromptBundle(draft) {
  return {
    brand: { prompt: draft.prompts.brand || '' },
    scenario: { prompt: draft.prompts.scenario || '' },
    product: { prompt: draft.prompts.product || '' },
    gallery: { prompt: draft.prompts.benefits || '' },
  };
}

function buildPosterInput(draft) {
  const ensure = (value, fallback) => (value && value.trim()) || fallback;
  const heroUrl = draft.assets.heroImage || draft.assets.brandLogo || FALLBACK_IMAGE;
  const productUrl = draft.assets.productImage || heroUrl || FALLBACK_IMAGE;
  const logoUrl = draft.assets.brandLogo || FALLBACK_IMAGE;

  const features = (draft.texts.highlights || '')
    .split(/\n|；|;|，|,/)
    .map((t) => t.trim())
    .filter(Boolean);
  while (features.length < 3) {
    features.push(`Feature ${features.length + 1}`);
  }

  const galleryItems = ['gallery1', 'gallery2', 'gallery3', 'gallery4'].map((key, idx) => {
    const asset = draft.assets[key];
    if (asset) {
      return { caption: `系列小图 ${idx + 1}`, asset, mode: 'upload', prompt: null };
    }
    return { caption: `系列小图 ${idx + 1}`, asset: logoUrl, mode: 'logo_fallback', prompt: null };
  });

  return {
    template_id: draft.layoutId || 'template_dual',
    brand_name: ensure(draft.texts.brand, 'Brand Name'),
    agent_name: ensure(draft.texts.brand, 'Channel Partner'),
    scenario_image: ensure(heroUrl, FALLBACK_IMAGE),
    product_name: ensure(draft.texts.slogan, 'Product'),
    features,
    title: ensure(draft.texts.slogan, '营销标题'),
    series_description: ensure(draft.texts.highlights, '系列卖点描述'),
    subtitle: ensure(draft.texts.cta, '副标题'),
    brand_logo: logoUrl,
    brand_logo_key: null,
    scenario_asset: heroUrl,
    product_asset: productUrl,
    scenario_key: null,
    product_key: null,
    gallery_items: galleryItems,
  };
}

function buildGenerateRequest(draft) {
  return {
    poster: buildPosterInput(draft),
    render_mode: 'locked',
    variants: 1,
    seed: null,
    lock_seed: false,
    prompt_bundle: buildPromptBundle(draft),
  };
}

async function callGeneratePoster(draft) {
  const apiBase = getApiBase();
  if (!apiBase) {
    alert('请先填写后端 API 地址');
    return null;
  }
  try {
    const payload = buildGenerateRequest(draft);
    return await postJson(apiBase, '/api/generate-poster', payload);
  } catch (err) {
    console.error('generate poster failed', err);
    alert(err.message || '生成失败，请检查后端服务');
    return null;
  }
}

function renderVariantB(draft) {
  const bRoot = document.getElementById('ab-preview-B');
  if (!bRoot) return;
  bRoot.innerHTML = '';
  if (draft.assets.posterUrl) {
    const img = document.createElement('img');
    img.src = draft.assets.posterUrl;
    img.alt = 'B 版海报';
    img.className = 'ab-poster-image';
    bRoot.appendChild(img);
  } else {
    bRoot.textContent = '当前没有 B 版海报，请先生成或选择 A 版。';
  }
}

function setLayoutPreviewText(text) {
  const layoutTextEls = [
    document.getElementById('layout-preview-text'),
    document.getElementById('layout-structure-text'),
  ];
  layoutTextEls.forEach((el) => {
    if (el) el.textContent = text || '';
  });
}

async function requestLayoutPreview(draft) {
  const apiBase = getApiBase();
  if (!apiBase) {
    alert('请先填写后端 API 地址');
    return;
  }
  try {
    const payload = buildGenerateRequest(draft);
    const resp = await postJson(apiBase, '/api/generate-poster', payload);
    if (resp?.layout_preview) {
      setLayoutPreviewText(resp.layout_preview);
    }
    return resp;
  } catch (err) {
    console.error('layout preview failed', err);
    alert(err.message || '调用后端预览失败');
  }
}

function updateVariantBRadio(draft) {
  const radioB = document.querySelector('input[name="posterAttachmentVariant"][value="B"]');
  const hint = document.getElementById('variant-b-note');
  if (!radioB || !hint) return;
  if (!draft.assets.posterUrl) {
    radioB.disabled = true;
    hint.textContent = '当前没有 B 版海报，默认使用 A 版。';
  } else {
    radioB.disabled = false;
    hint.textContent = '';
  }
}

function persistAttachmentChoice(draft) {
  const checked = document.querySelector('input[name="posterAttachmentVariant"]:checked');
  const variant = checked ? checked.value : 'A';
  let url = draft.assets.heroImage;
  let name = 'poster_A.png';
  let effective = 'A';
  if (variant === 'B' && draft.assets.posterUrl) {
    url = draft.assets.posterUrl;
    name = 'poster_B.png';
    effective = 'B';
  }
  localStorage.setItem('poster_attachment_variant', effective);
  localStorage.setItem('poster_attachment_url', url || '');
  localStorage.setItem('poster_attachment_name', name);
}

function initStage1() {
  const draft = loadDraft();
  bindApiBaseInput();
  const layoutPicker = document.getElementById('layout-picker');
  renderLayoutCards(layoutPicker, draft.layoutId);
  applyLayoutSelection(layoutPicker, draft, () => {
    saveDraft(draft);
    renderPosterPreview(document.getElementById('poster-layout-preview'), draft);
  });
  const previewRoot = document.getElementById('poster-layout-preview');
  attachTextListeners(draft, previewRoot);
  attachFileListeners(draft, previewRoot);
  attachPromptListeners(draft);
  renderPosterPreview(previewRoot, draft);
  renderPromptPreview(draft);
  setLayoutPreviewText(draft.layoutPreview || '');

  const nextBtn = document.getElementById('go-to-stage2');
  if (nextBtn) {
    nextBtn.addEventListener('click', (e) => {
      e.preventDefault();
      saveDraft(draft);
      window.location.href = 'stage2.html';
    });
  }

  const previewBtn = document.getElementById('preview-layout');
  if (previewBtn) {
    previewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      saveDraft(draft);
      void requestLayoutPreview(draft).then((resp) => {
        if (resp?.layout_preview) {
          draft.layoutPreview = resp.layout_preview;
          saveDraft(draft);
        }
      });
    });
  }
}

function initStage2() {
  const draft = loadDraft();
  bindApiBaseInput();
  const previewRoot = document.getElementById('ab-preview-variant-a');
  const layoutPicker = document.getElementById('layout-picker-stage2');
  renderLayoutCards(layoutPicker, draft.layoutId);
  applyLayoutSelection(layoutPicker, draft, () => {
    saveDraft(draft);
    renderPosterPreview(previewRoot, draft);
  });
  renderPosterPreview(previewRoot, draft);
  renderPromptPreview(draft);
  updateVariantBRadio(draft);
  renderVariantB(draft);
  setLayoutPreviewText(draft.layoutPreview || '');

  const generateBtn = document.getElementById('generate-poster');
  if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
      const resp = await callGeneratePoster(draft);
      if (!resp) return;
      draft.assets.heroImage = resp.scenario_image?.url || draft.assets.heroImage;
      draft.assets.productImage = resp.product_image?.url || draft.assets.productImage;
      const gallery = resp.gallery_images?.map((g) => g.url) || [];
      ['gallery1', 'gallery2', 'gallery3', 'gallery4'].forEach((key, idx) => {
        draft.assets[key] = gallery[idx] || draft.assets[key] || draft.assets.brandLogo;
      });
      draft.assets.posterUrl = resp.poster_url || draft.assets.posterUrl;
      if (resp.layout_preview) {
        setLayoutPreviewText(resp.layout_preview);
        draft.layoutPreview = resp.layout_preview;
      }
      saveDraft(draft);
      renderPosterPreview(previewRoot, draft);
      renderVariantB(draft);
      updateVariantBRadio(draft);
    });
  }

  const regenerateBtn = document.getElementById('regenerate-poster');
  if (regenerateBtn) {
    regenerateBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (generateBtn) generateBtn.click();
    });
  }

  const previewPromptsBtn = document.getElementById('preview-prompts');
  if (previewPromptsBtn) {
    previewPromptsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const payload = buildGenerateRequest(draft);
      alert(JSON.stringify(payload.prompt_bundle, null, 2));
    });
  }

  const goStage3 = document.getElementById('go-to-stage3');
  if (goStage3) {
    goStage3.addEventListener('click', (e) => {
      e.preventDefault();
      persistAttachmentChoice(draft);
      saveDraft(draft);
      window.location.href = 'stage3.html';
    });
  }
}

function initStage3() {
  bindApiBaseInput();
  const variant = localStorage.getItem('poster_attachment_variant') || 'A';
  const url = localStorage.getItem('poster_attachment_url');
  const name = localStorage.getItem('poster_attachment_name') || 'poster.png';
  const indicator = document.getElementById('attachment-variant-indicator');
  if (indicator) {
    indicator.textContent = `当前附件：${variant} 版海报`;
  }
  const attachmentPreview = document.getElementById('attachment-preview');
  if (attachmentPreview && url) {
    attachmentPreview.src = url;
  }

  const emailForm = document.getElementById('email-form');
  if (emailForm) {
    emailForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const apiBase = getApiBase();
      if (!apiBase) {
        alert('请先填写后端 API 地址');
        return;
      }
      const recipient = document.getElementById('email-recipient')?.value?.trim();
      const subject = document.getElementById('email-subject')?.value?.trim() || '营销海报';
      const body = document.getElementById('email-body')?.value?.trim() || '请查收海报附件。';
      if (!recipient) {
        alert('请填写收件人邮箱');
        return;
      }

      const attachment = url
        ? {
            filename: name,
            media_type: 'image/png',
            url,
            width: 1024,
            height: 1024,
          }
        : null;

      try {
        const resp = await postJson(apiBase, '/api/send-email', {
          recipient,
          subject,
          body,
          attachment,
        });
        alert(resp?.detail || '邮件请求已发送');
      } catch (err) {
        console.error('send email failed', err);
        alert(err.message || '邮件发送失败');
      }
    });
  }
}

function bootstrap() {
  const stage = document.body.dataset.stage;
  if (stage === 'stage1') return initStage1();
  if (stage === 'stage2') return initStage2();
  if (stage === 'stage3') return initStage3();
}

document.addEventListener('DOMContentLoaded', bootstrap);
