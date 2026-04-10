const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildPoster2PayloadFromNormalisedInputs,
  buildPoster2RequestSummary,
  buildStage2SourceSignatures,
  createRequestCoordinator,
  diffPayloadPaths,
  stableStringify,
} = require('../../frontend/stage2_request_helpers.js');

function makeInput(overrides = {}) {
  return {
    templateId: 'template_dual_v2',
    rendererMode: 'auto',
    brandName: 'ChefCraft',
    agentName: 'North Kitchen',
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat', 'Easy clean'],
    productImage: { url: 'https://cdn.example.com/product-a.png', key: 'product-a' },
    productSecondaryImage: { url: 'https://cdn.example.com/product-b.png', key: 'product-b' },
    logo: { url: 'https://cdn.example.com/logo.png', key: 'logo' },
    scenarioImage: { url: 'https://cdn.example.com/scenario-a.png', key: 'scenario-a' },
    galleryImages: [
      { url: 'https://cdn.example.com/gallery-1.png', key: 'gallery-1', caption: 'Front' },
      { url: 'https://cdn.example.com/gallery-2.png', key: 'gallery-2', caption: 'Angle' },
    ],
    bottomRequestState: {
      gallery_input_count_raw: 2,
      gallery_input_count_normalized: 2,
      requested_gallery_count: 2,
      gallery_autofill_applied: false,
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
    },
    stylePrompt: 'clean studio background',
    copyOptimization: {
      mode: 'off',
      decision: 'pending',
      acceptedFeatures: [],
    },
    ...overrides,
  };
}

test('repeated same-input generate produces identical payloads', () => {
  const payloadA = buildPoster2PayloadFromNormalisedInputs(makeInput());
  const payloadB = buildPoster2PayloadFromNormalisedInputs(makeInput());
  assert.equal(stableStringify(payloadA), stableStringify(payloadB));
});

test('scenario-only change affects only scenario fields', () => {
  const before = buildPoster2PayloadFromNormalisedInputs(makeInput());
  const after = buildPoster2PayloadFromNormalisedInputs(
    makeInput({
      scenarioImage: { url: 'https://cdn.example.com/scenario-b.png', key: 'scenario-b' },
    })
  );
  assert.deepEqual(diffPayloadPaths(before, after), ['$.scenario_image.key', '$.scenario_image.url']);
});

test('gallery-only change affects only gallery fields', () => {
  const before = buildPoster2PayloadFromNormalisedInputs(makeInput());
  const after = buildPoster2PayloadFromNormalisedInputs(
    makeInput({
      galleryImages: [
        { url: 'https://cdn.example.com/gallery-9.png', key: 'gallery-9', caption: 'New 1' },
        { url: 'https://cdn.example.com/gallery-8.png', key: 'gallery-8', caption: 'New 2' },
      ],
    })
  );
  const diff = diffPayloadPaths(before, after);
  assert(diff.every((entry) => entry.startsWith('$.gallery_images[')));
});

test('copy-only change affects only text-related fields', () => {
  const before = buildPoster2PayloadFromNormalisedInputs(makeInput());
  const after = buildPoster2PayloadFromNormalisedInputs(
    makeInput({
      title: 'Air Fryer Pro',
      subtitle: 'Sharper copy',
      features: ['Fast heat', 'Easy clean', 'Quiet mode'],
      stylePrompt: 'commercial kitchen lighting',
      copyOptimization: {
        mode: 'suggest',
        decision: 'accepted',
        acceptedTitle: 'Air Fryer Pro',
        acceptedSubtitle: 'Sharper copy',
        acceptedFeatures: ['Fast heat', 'Easy clean', 'Quiet mode'],
      },
    })
  );
  assert.deepEqual(diffPayloadPaths(before, after), [
    '$.copy_optimization.accepted_features[0]',
    '$.copy_optimization.accepted_features[1]',
    '$.copy_optimization.accepted_features[2]',
    '$.copy_optimization.accepted_subtitle',
    '$.copy_optimization.accepted_title',
    '$.copy_optimization.decision',
    '$.copy_optimization.mode',
    '$.features[2]',
    '$.style.prompt',
    '$.subtitle',
    '$.title',
  ]);
});

test('latest request coordinator invalidates older in-flight request', () => {
  const coordinator = createRequestCoordinator();
  const request1 = coordinator.start();
  const request2 = coordinator.start();
  assert.equal(coordinator.isCurrent(request1), false);
  assert.equal(coordinator.isCurrent(request2), true);
});

test('replaced assets do not keep stale URLs in next payload', () => {
  const before = buildPoster2PayloadFromNormalisedInputs(makeInput());
  const after = buildPoster2PayloadFromNormalisedInputs(
    makeInput({
      scenarioImage: { url: 'https://cdn.example.com/scenario-fresh.png', key: 'scenario-fresh' },
      productImage: { url: 'https://cdn.example.com/product-fresh.png', key: 'product-fresh' },
      galleryImages: [{ url: 'https://cdn.example.com/gallery-fresh.png', key: 'gallery-fresh', caption: 'Fresh' }],
    })
  );
  const afterJson = stableStringify(after);
  assert(!afterJson.includes(before.scenario_image.url));
  assert(!afterJson.includes(before.product_image.url));
  before.gallery_images.forEach((entry) => {
    assert(!afterJson.includes(entry.url));
  });
});

test('source signatures isolate asset changes from copy changes', () => {
  const before = buildStage2SourceSignatures({
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  });
  const afterScenario = buildStage2SourceSignatures({
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-b.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  });
  const afterCopy = buildStage2SourceSignatures({
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
    title: 'Air Fryer Pro',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  });
  assert.notEqual(before.assetSignature, afterScenario.assetSignature);
  assert.equal(before.copySignature, afterScenario.copySignature);
  assert.equal(before.assetSignature, afterCopy.assetSignature);
  assert.notEqual(before.copySignature, afterCopy.copySignature);
});

test('request summary stays normalized and Template A contract fields unchanged', () => {
  const payload = buildPoster2PayloadFromNormalisedInputs(makeInput());
  assert.deepEqual(buildPoster2RequestSummary(payload), {
    template_id: 'template_dual_v2',
    renderer_mode: 'auto',
    bottom_mode: 'title_gallery_split',
    gallery_mode: 'strip_local_visible_only',
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    feature_count: 2,
    gallery_count: 2,
    logo_url: 'https://cdn.example.com/logo.png',
    scenario_url: 'https://cdn.example.com/scenario-a.png',
    product_url: 'https://cdn.example.com/product-a.png',
    gallery_urls: [
      'https://cdn.example.com/gallery-1.png',
      'https://cdn.example.com/gallery-2.png',
    ],
    copy_optimization_decision: 'pending',
  });
});
