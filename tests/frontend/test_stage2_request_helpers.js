const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildPoster2PayloadFromNormalisedInputs,
  buildGeneratePosterPayloadFromForm,
  buildPoster2RequestSummary,
  buildStage2SourceSignatures,
  buildStage2FormStateSignatures,
  diffStage2FormSignatures,
  countStage1GalleryAssets,
  buildStage2PreflightDiagnostics,
  classifyStoredStage2ResultCompatibility,
  classifyStage2RequestFailure,
  hashStableValue,
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

test('buildGeneratePosterPayloadFromForm returns a fresh request snapshot each time', () => {
  const input = makeInput();
  const payloadA = buildGeneratePosterPayloadFromForm(input);
  const payloadB = buildGeneratePosterPayloadFromForm(input);

  assert.notEqual(payloadA, payloadB);
  assert.notEqual(payloadA.features, payloadB.features);
  assert.notEqual(payloadA.gallery_images, payloadB.gallery_images);
  assert.notEqual(payloadA.copy_optimization, payloadB.copy_optimization);
  assert.notEqual(payloadA.copy_optimization.accepted_features, payloadB.copy_optimization.accepted_features);
  assert.equal(stableStringify(payloadA), stableStringify(payloadB));
});

test('buildGeneratePosterPayloadFromForm does not let old derived arrays contaminate the next payload', () => {
  const first = buildGeneratePosterPayloadFromForm(
    makeInput({
      features: ['First A', 'First B'],
      galleryImages: [
        { url: 'https://cdn.example.com/old-gallery.png', key: 'old-gallery', caption: 'Old' },
      ],
      copyOptimization: {
        mode: 'suggest',
        decision: 'accepted',
        acceptedFeatures: ['Accepted old'],
      },
    })
  );
  first.features.push('mutated old feature');
  first.gallery_images.push({ url: 'https://cdn.example.com/mutated-old.png', key: 'mutated-old' });
  first.copy_optimization.accepted_features.push('mutated old accepted');

  const second = buildGeneratePosterPayloadFromForm(
    makeInput({
      features: ['Second A'],
      galleryImages: [
        { url: 'https://cdn.example.com/new-gallery.png', key: 'new-gallery', caption: 'New' },
      ],
      copyOptimization: {
        mode: 'suggest',
        decision: 'pending',
        acceptedFeatures: [],
      },
    })
  );
  const secondJson = stableStringify(second);
  assert(!secondJson.includes('old-gallery'));
  assert(!secondJson.includes('mutated-old'));
  assert(!secondJson.includes('Accepted old'));
  assert(!secondJson.includes('mutated old'));
  assert.deepEqual(second.features, ['Second A']);
  assert.deepEqual(second.gallery_images.map((entry) => entry.url), ['https://cdn.example.com/new-gallery.png']);
  assert.deepEqual(second.copy_optimization.accepted_features, []);
});

test('buildGeneratePosterPayloadFromForm ignores success response metadata fields', () => {
  const payload = buildGeneratePosterPayloadFromForm(
    makeInput({
      poster_key: 'poster/success/old.png',
      final_url: 'https://cdn.example.com/success-old.png',
      bottom_contract_review: {
        bottom_mode: 'gallery_only',
      },
      copy_optimization_review: {
        title: { optimized_text: 'Old optimized title' },
      },
      previewTruth: {
        bottomMode: 'gallery_only',
      },
      latestResult: {
        bottom_contract_review: { bottom_mode: 'gallery_only' },
      },
    })
  );
  const payloadJson = stableStringify(payload);
  assert(!payloadJson.includes('poster/success/old.png'));
  assert(!payloadJson.includes('success-old.png'));
  assert(!payloadJson.includes('Old optimized title'));
  assert(!payloadJson.includes('previewTruth'));
  assert.equal(payload.bottom_contract_review, undefined);
  assert.equal(payload.copy_optimization_review, undefined);
  assert.equal(payload.poster_key, undefined);
  assert.equal(payload.final_url, undefined);
  assert.equal(payload.previewTruth, undefined);
  assert.equal(payload.latestResult, undefined);
});

test('stale thumbnails override does not enter payload counts', () => {
  const payload = buildGeneratePosterPayloadFromForm(
    makeInput({
      thumbnails: 4,
      galleryCount: 4,
      bottomRequestState: {
        gallery_input_count_raw: 4,
        gallery_input_count_normalized: 4,
        requested_gallery_count: 4,
        gallery_autofill_applied: true,
        auto_fill_gallery: true,
        bottom_mode: 'title_gallery_split',
        gallery_mode: 'strip_local_visible_only',
      },
      galleryImages: [
        { url: 'https://cdn.example.com/gallery-current-1.png', key: 'gallery-current-1', caption: 'Current 1' },
        { url: 'https://cdn.example.com/gallery-current-2.png', key: 'gallery-current-2', caption: 'Current 2' },
        { url: 'https://cdn.example.com/gallery-current-3.png', key: 'gallery-current-3', caption: 'Current 3' },
      ],
    })
  );
  assert.equal(payload.gallery_requested_count, 3);
  assert.equal(payload.gallery_input_count_raw, 3);
  assert.equal(payload.gallery_input_count_normalized, 3);
  assert.equal(payload.gallery_autofill_applied, false);
  assert.equal(payload.thumbnails, undefined);
  assert.equal(payload.galleryCount, undefined);
});

test('changing stale thumbnails value without changing assets has no effect', () => {
  const base = {
    galleryImages: [
      { url: 'https://cdn.example.com/gallery-current-1.png', key: 'gallery-current-1', caption: 'Current 1' },
      { url: 'https://cdn.example.com/gallery-current-2.png', key: 'gallery-current-2', caption: 'Current 2' },
      { url: 'https://cdn.example.com/gallery-current-3.png', key: 'gallery-current-3', caption: 'Current 3' },
    ],
    bottomRequestState: {
      gallery_input_count_raw: 4,
      gallery_input_count_normalized: 4,
      requested_gallery_count: 4,
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
    },
  };
  const payloadA = buildGeneratePosterPayloadFromForm(makeInput({ ...base, thumbnails: 4 }));
  const payloadB = buildGeneratePosterPayloadFromForm(makeInput({ ...base, thumbnails: 1 }));
  assert.equal(stableStringify(payloadA), stableStringify(payloadB));
  assert.equal(payloadA.gallery_requested_count, 3);
});

test('form signatures ignore stale gallery-count overrides and follow Stage1 gallery assets', () => {
  const stage1Data = {
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [
      { asset: { url: 'https://cdn.example.com/gallery-1.png' }, caption: 'One' },
      { asset: { url: 'https://cdn.example.com/gallery-2.png' }, caption: 'Two' },
      { asset: { url: 'https://cdn.example.com/gallery-3.png' }, caption: 'Three' },
    ],
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  };
  const signature = buildStage2FormStateSignatures({
    stage1Data,
    bottomRequestState: {
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
      requested_gallery_count: 99,
      gallery_input_count_raw: 88,
      gallery_input_count_normalized: 77,
      gallery_autofill_applied: true,
      auto_fill_gallery: true,
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });
  assert.equal(signature.bottom.requested_gallery_count, 3);
  assert.equal(signature.bottom.gallery_input_count_raw, 3);
  assert.equal(signature.bottom.gallery_input_count_normalized, 3);
  assert.equal(signature.bottom.gallery_autofill_applied, false);
  assert.equal(signature.bottom.auto_fill_gallery, false);
  assert.equal(signature.canonicalForm.detected_gallery_items, 3);
  assert.equal(
    signature.canonicalForm.detected_gallery_assets_signature,
    stableStringify([
      'https://cdn.example.com/gallery-1.png',
      'https://cdn.example.com/gallery-2.png',
      'https://cdn.example.com/gallery-3.png',
    ])
  );
});

test('gallery count follows Stage1 asset truth across supported bottom modes', () => {
  const makeGallery = (count) =>
    Array.from({ length: count }, (_, index) => ({
      url: `https://cdn.example.com/gallery-${index + 1}.png`,
      key: `gallery-${index + 1}`,
      caption: `Gallery ${index + 1}`,
    }));
  for (const [mode, count] of [
    ['title_gallery_split', 4],
    ['title_gallery_split', 3],
    ['gallery_only', 4],
    ['gallery_only', 3],
    ['text_only_expanded', 3],
  ]) {
    const payload = buildGeneratePosterPayloadFromForm(
      makeInput({
        galleryImages: makeGallery(count),
        bottomRequestState: {
          gallery_input_count_raw: 4,
          gallery_input_count_normalized: 4,
          requested_gallery_count: 4,
          bottom_mode: mode,
          gallery_mode: 'strip_local_visible_only',
        },
      })
    );
    assert.equal(payload.bottom_mode, mode);
    assert.equal(payload.gallery_images.length, count);
    assert.equal(payload.gallery_requested_count, count);
    assert.equal(payload.gallery_input_count_raw, count);
    assert.equal(payload.gallery_input_count_normalized, count);
  }
});

test('Stage1 gallery asset count ignores stale empty slots', () => {
  assert.equal(
    countStage1GalleryAssets({
      gallery_entries: [
        { asset: { url: 'https://cdn.example.com/gallery-1.png' }, caption: 'One' },
        { asset: null, caption: 'Empty' },
        { asset: {}, caption: 'Empty object' },
        { asset: { key: 'gallery-3' }, caption: 'Three' },
        { asset: { dataUrl: 'data:image/png;base64,abc' }, caption: 'Four' },
      ],
    }),
    3
  );
});

test('form signatures mark bottom changes without asset or copy changes', () => {
  const stage1Data = {
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  };
  const before = buildStage2FormStateSignatures({
    stage1Data,
    bottomRequestState: {
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
      requested_gallery_count: 2,
      gallery_input_count_raw: 2,
      gallery_input_count_normalized: 2,
      gallery_autofill_applied: false,
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });
  const after = buildStage2FormStateSignatures({
    stage1Data,
    bottomRequestState: {
      bottom_mode: 'gallery_only',
      gallery_mode: 'strip_local_visible_only',
      requested_gallery_count: 4,
      gallery_input_count_raw: 4,
      gallery_input_count_normalized: 1,
      gallery_autofill_applied: true,
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });
  assert.deepEqual(diffStage2FormSignatures(before, after), ['bottom_contract']);
});

test('switching bottom_mode after success produces invalidated preflight state', () => {
  const stage1Data = {
    brand_logo: { url: 'https://cdn.example.com/logo.png' },
    scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
    product_image_1: { url: 'https://cdn.example.com/product-a.png' },
    gallery_entries: [
      { asset: { url: 'https://cdn.example.com/gallery-1.png' }, caption: 'One' },
      { asset: { url: 'https://cdn.example.com/gallery-2.png' }, caption: 'Two' },
      { asset: { url: 'https://cdn.example.com/gallery-3.png' }, caption: 'Three' },
      { asset: { url: 'https://cdn.example.com/gallery-4.png' }, caption: 'Four' },
    ],
    title: 'Air Fryer',
    subtitle: 'Crisp results',
    features: ['Fast heat'],
  };
  const makeSignature = (mode) =>
    buildStage2FormStateSignatures({
      stage1Data,
      bottomRequestState: {
        bottom_mode: mode,
        gallery_mode: 'strip_local_visible_only',
        requested_gallery_count: 4,
        gallery_input_count_raw: 4,
        gallery_input_count_normalized: 4,
        gallery_autofill_applied: false,
        requested_title_text: 'Air Fryer',
        requested_subtitle_text: 'Crisp results',
      },
      copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
      adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
    });

  const success = makeSignature('title_gallery_split');
  const galleryOnly = makeSignature('gallery_only');
  const backToSplit = makeSignature('title_gallery_split');
  const textOnly = makeSignature('text_only_expanded');

  assert.deepEqual(diffStage2FormSignatures(success, galleryOnly), ['bottom_contract']);
  assert.deepEqual(diffStage2FormSignatures(galleryOnly, backToSplit), ['bottom_contract']);
  assert.deepEqual(diffStage2FormSignatures(success, textOnly), ['bottom_contract']);
  assert.deepEqual(diffStage2FormSignatures(textOnly, backToSplit), ['bottom_contract']);

  const payload = buildGeneratePosterPayloadFromForm(
    makeInput({
      bottomRequestState: {
        bottom_mode: 'gallery_only',
        gallery_mode: 'strip_local_visible_only',
        requested_gallery_count: 4,
        gallery_input_count_raw: 4,
        gallery_input_count_normalized: 4,
      },
      galleryImages: stage1Data.gallery_entries.map((entry, index) => ({
        url: entry.asset.url,
        key: `gallery-${index + 1}`,
        caption: entry.caption,
      })),
    })
  );
  const diagnostics = buildStage2PreflightDiagnostics({
    requestId: 7,
    formSignatures: galleryOnly,
    payload,
    previousSuccessPresent: true,
    invalidatedFields: diffStage2FormSignatures(success, galleryOnly),
    clearedSuccessState: true,
    detectedGalleryItems: 4,
  });
  assert.equal(diagnostics.request_id, 7);
  assert.equal(diagnostics.current_bottom_mode, 'gallery_only');
  assert.equal(diagnostics.previous_success_present, true);
  assert.equal(diagnostics.cleared_success_state, true);
  assert.deepEqual(diagnostics.invalidated_fields, ['bottom_contract']);
  assert.equal(diagnostics.detected_gallery_items, 4);
  assert.equal(diagnostics.canonical_form_signature, galleryOnly.formSignature);
  assert.equal(diagnostics.canonical_form_signature_hash, hashStableValue(galleryOnly.formSignature));
  assert.equal(diagnostics.request_payload_signature, stableStringify(payload));
  assert.equal(diagnostics.request_payload_signature_hash, hashStableValue(payload));
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

test('stored Stage2 success is rejected when canonical signature no longer matches current Stage1 truth', () => {
  const current = buildStage2FormStateSignatures({
    stage1Data: {
      brand_logo: { url: 'https://cdn.example.com/logo-a.png' },
      scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
      product_image_1: { url: 'https://cdn.example.com/product-a.png' },
      gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
      title: 'Air Fryer',
      subtitle: 'Crisp results',
      features: ['Fast heat'],
    },
    bottomRequestState: {
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });
  const stale = buildStage2FormStateSignatures({
    stage1Data: {
      brand_logo: { url: 'https://cdn.example.com/logo-a.png' },
      scenario_asset: { url: 'https://cdn.example.com/scenario-b.png' },
      product_image_1: { url: 'https://cdn.example.com/product-a.png' },
      gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
      title: 'Air Fryer',
      subtitle: 'Crisp results',
      features: ['Fast heat'],
    },
    bottomRequestState: {
      bottom_mode: 'title_gallery_split',
      gallery_mode: 'strip_local_visible_only',
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });

  const compatibility = classifyStoredStage2ResultCompatibility(
    {
      poster_key: 'poster-stale',
      canonical_form_signature: stale.formSignature,
    },
    current.formSignature
  );

  assert.equal(compatibility.compatible, false);
  assert.equal(compatibility.reason, 'canonical_signature_mismatch');
  assert.equal(compatibility.shouldClearPosterKey, true);
});

test('stored Stage2 success stays compatible only when canonical signature still matches', () => {
  const current = buildStage2FormStateSignatures({
    stage1Data: {
      brand_logo: { url: 'https://cdn.example.com/logo-a.png' },
      scenario_asset: { url: 'https://cdn.example.com/scenario-a.png' },
      product_image_1: { url: 'https://cdn.example.com/product-a.png' },
      gallery_entries: [{ asset: { url: 'https://cdn.example.com/gallery-a.png' }, caption: 'A' }],
      title: 'Air Fryer',
      subtitle: 'Crisp results',
      features: ['Fast heat'],
    },
    bottomRequestState: {
      bottom_mode: 'gallery_only',
      gallery_mode: 'strip_local_visible_only',
      requested_title_text: 'Air Fryer',
      requested_subtitle_text: 'Crisp results',
    },
    copyOptimization: { mode: 'suggest', decision: 'pending', acceptedFeatures: [] },
    adjustments: { showBullets: true, titleSize: 'M', qualityMode: 'stable' },
  });

  const compatibility = classifyStoredStage2ResultCompatibility(
    {
      poster_key: 'poster-current',
      canonical_form_signature: current.formSignature,
    },
    current.formSignature
  );

  assert.equal(compatibility.compatible, true);
  assert.equal(compatibility.reason, 'canonical_signature_match');
  assert.equal(compatibility.shouldClearPosterKey, false);
});

test('request failure classification separates request-state, network transport, and backend unavailable', () => {
  const requestFailure = classifyStage2RequestFailure({
    status: 422,
    responseJson: { detail: { error: 'image_decode_failed', message: 'bad placeholder asset' } },
  });
  assert.equal(requestFailure.kind, 'request_state');
  assert.match(requestFailure.operatorMessage, /素材或输入/);

  const fetchFailure = classifyStage2RequestFailure(new TypeError('Failed to fetch'));
  assert.equal(fetchFailure.kind, 'network_transport');
  assert.match(fetchFailure.operatorMessage, /浏览器未能完成生成请求/);

  const corsFailure = classifyStage2RequestFailure({
    status: 0,
    message: 'CORS blocked by Access-Control-Allow-Origin',
  });
  assert.equal(corsFailure.kind, 'network_transport');
  assert.match(corsFailure.operatorMessage, /跨域|预检/);

  const backendFailure = classifyStage2RequestFailure({
    status: 502,
    responseJson: { detail: { error: 'asset_fetch_timeout', message: 'upstream timeout' } },
  });
  assert.equal(backendFailure.kind, 'backend_unavailable');
  assert.match(backendFailure.operatorMessage, /服务暂时不可用|服务器错误/);
});
