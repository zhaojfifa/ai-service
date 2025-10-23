import { generatePoster } from './api.js';

function loadAssetsFromStage1() {
  const raw = localStorage.getItem('stage1-assets');
  return raw ? JSON.parse(raw) : { scenario: null, product: null, gallery: [] };
}

export async function onClickGenerate() {
  const assets = loadAssetsFromStage1();

  const payload = {
    poster: {
      template_id: 'template_dual',
      brand_name: 'ChefCraft',
      agent_name: 'Star Service Hub',
      scenario_mode: 'upload',
      scenario_asset: assets.scenario
        ? { key: assets.scenario.key, url: assets.scenario.url }
        : null,
      product_mode: 'upload',
      product_asset: assets.product
        ? { key: assets.product.key, url: assets.product.url }
        : null,
      gallery_items: (assets.gallery || []).map((item) => ({
        caption: 'item',
        mode: 'upload',
        asset: { key: item.key, url: item.url },
      })),
      features: [
        'One-tap steam & roast',
        '360° smart convection',
        'Self-cleaning cavity',
        'Wi-Fi remote control',
      ],
      title: 'Upgrade Kitchen Speed, Create Chef-Grade Flavor',
      subtitle: 'Smart Steam & Roast · Effortless Banquet Control',
    },
    variants: 2,
  };

  const json = JSON.stringify(payload);
  if (json.includes('data:image/')) {
    throw new Error('payload contains base64; abort');
  }

  console.log('[generate] payload', payload);
  const result = await generatePoster(payload);
  console.log('[generate] response', result);

  const url = result?.cdn_url || result?.url || result?.public_url;
  if (url) {
    const img = document.createElement('img');
    img.src = url;
    img.style.maxWidth = '640px';
    const container = document.querySelector('#poster-result');
    if (container) {
      container.innerHTML = '';
      container.appendChild(img);
    }
  }
}
