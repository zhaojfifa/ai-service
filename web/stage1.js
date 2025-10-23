import { presignPut, putToR2 } from './api.js';

const state = {
  assets: {
    scenario: null,
    product: null,
    gallery: [],
  },
};

function $(selector) {
  return document.querySelector(selector);
}

export async function handlePickFile(inputEl, slot = 'scenario') {
  const file = inputEl.files?.[0];
  if (!file) return;

  const presign = await presignPut(file.name, file.type, 'assets/user');

  await putToR2(presign.upload_url, file);

  const ref = {
    key: presign.key,
    url: presign.public_url,
    name: file.name,
    size: file.size,
    type: file.type,
  };
  if (slot === 'scenario') {
    state.assets.scenario = ref;
  } else if (slot === 'product') {
    state.assets.product = ref;
  } else {
    state.assets.gallery.push(ref);
  }

  const img = document.createElement('img');
  img.src = presign.public_url;
  img.style.maxWidth = '160px';
  const preview = $(`#preview-${slot}`);
  if (preview) {
    preview.innerHTML = '';
    preview.appendChild(img);
  }

  localStorage.setItem('stage1-assets', JSON.stringify(state.assets));
  console.log('[upload] done', ref);
}
