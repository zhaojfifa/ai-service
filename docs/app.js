/*
 * Route A front-end for ai-service (GitHub Pages)
 * Stage 1: layout selection + content entry + slot image uploads
 * Stage 2: reuse same layout, optionally call backend to generate images/text
 * Shared state is stored in localStorage under ROUTE_A_DRAFT_KEY
 */

const ROUTE_A_DRAFT_KEY = 'routeA.posterDraft';

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
  };
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(ROUTE_A_DRAFT_KEY);
    if (!raw) return getDefaultDraft();
    const parsed = JSON.parse(raw);
    return { ...getDefaultDraft(), ...parsed, texts: { ...getDefaultDraft().texts, ...parsed.texts }, assets: { ...getDefaultDraft().assets, ...parsed.assets }, prompts: { ...getDefaultDraft().prompts, ...parsed.prompts } };
  } catch (e) {
    console.warn('failed to load draft', e);
    return getDefaultDraft();
  }
}

function saveDraft(draft) {
  localStorage.setItem(ROUTE_A_DRAFT_KEY, JSON.stringify(draft));
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
  if (logoImg) logoImg.src = draft.assets.brandLogo || '';

  const heroImg = container.querySelector('[data-slot="hero"]');
  if (heroImg) heroImg.src = draft.assets.heroImage || '';

  const productImg = container.querySelector('[data-slot="product"]');
  if (productImg) productImg.src = draft.assets.productImage || '';

  const gallerySlots = container.querySelectorAll('[data-slot^="gallery-"]');
  gallerySlots.forEach((img, idx) => {
    const key = `gallery${idx + 1}`;
    img.src = draft.assets[key] || draft.assets.brandLogo || '';
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
      const url = await readFileAsDataUrl(file);
      draft.assets[key] = url;
      saveDraft(draft);
      renderPosterPreview(previewRoot, draft);
      const preview = document.querySelector(`[data-preview-for="${id}"]`);
      if (preview) preview.src = url;
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

function buildGeneratePayload(draft) {
  return {
    template_id: draft.layoutId,
    brand_name: draft.texts.brand,
    headline: draft.texts.slogan,
    tagline: draft.texts.cta,
    prompts: { ...draft.prompts },
    assets: { ...draft.assets },
  };
}

async function callGeneratePoster(draft) {
  const apiBase = document.getElementById('api-base')?.value?.trim();
  if (!apiBase) {
    alert('请先填写后端 API 地址');
    return null;
  }
  try {
    const payload = buildGeneratePayload(draft);
    const resp = await fetch(`${apiBase}/api/generate-poster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('generate poster failed', err);
    alert('生成失败，请检查后端服务');
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

  const nextBtn = document.getElementById('go-to-stage2');
  if (nextBtn) {
    nextBtn.addEventListener('click', (e) => {
      e.preventDefault();
      saveDraft(draft);
      window.location.href = 'stage2.html';
    });
  }
}

function initStage2() {
  const draft = loadDraft();
  const previewRoot = document.getElementById('poster-layout-preview');
  renderLayoutCards(document.getElementById('layout-picker-stage2'), draft.layoutId);
  renderPosterPreview(previewRoot, draft);
  renderPromptPreview(draft);
  updateVariantBRadio(draft);
  renderVariantB(draft);

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
      saveDraft(draft);
      renderPosterPreview(previewRoot, draft);
      renderVariantB(draft);
      updateVariantBRadio(draft);
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
  // email send form should already include logic to send attachment URL/name
}

function bootstrap() {
  const stage = document.body.dataset.stage;
  if (stage === 'stage1') return initStage1();
  if (stage === 'stage2') return initStage2();
  if (stage === 'stage3') return initStage3();
}

document.addEventListener('DOMContentLoaded', bootstrap);
