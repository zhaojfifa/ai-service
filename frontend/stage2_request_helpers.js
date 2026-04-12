(function initStage2RequestHelpers(globalScope) {
  function cloneValue(value) {
    if (typeof globalScope.structuredClone === 'function') {
      try {
        return globalScope.structuredClone(value);
      } catch (error) {
        console.warn('[stage2-request-helpers] structuredClone failed, falling back to JSON clone', error);
      }
    }
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
  }

  function normalizeText(value) {
    return typeof value === 'string' ? value.trim() : '';
  }

  function pickAssetIdentity(value) {
    if (!value) return null;
    if (typeof value === 'string') {
      const text = value.trim();
      return text || null;
    }
    if (Array.isArray(value)) {
      return value.map((entry) => pickAssetIdentity(entry)).filter(Boolean);
    }
    if (typeof value === 'object') {
      const direct = [
        value.key,
        value.r2Key,
        value.storage_key,
        value.url,
        value.remoteUrl,
        value.publicUrl,
        value.public_url,
        value.asset_url,
        value.src,
        value.dataUrl,
        value.data_url,
      ].find((entry) => normalizeText(entry));
      if (direct) return normalizeText(direct);
      return Object.keys(value)
        .sort()
        .reduce((acc, key) => {
          const next = pickAssetIdentity(value[key]);
          if (next == null || next === '') return acc;
          acc[key] = next;
          return acc;
        }, {});
    }
    return value;
  }

  function stableStringify(value) {
    const sortValue = (input) => {
      if (Array.isArray(input)) return input.map(sortValue);
      if (!input || typeof input !== 'object') return input;
      return Object.keys(input)
        .sort()
        .reduce((acc, key) => {
          acc[key] = sortValue(input[key]);
          return acc;
        }, {});
    };
    return JSON.stringify(sortValue(value));
  }

  function hashStableValue(value) {
    const text = typeof value === 'string' ? value : stableStringify(value);
    let hash = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16).padStart(8, '0');
  }

  function hasPickedAssetIdentity(value) {
    const identity = pickAssetIdentity(value);
    if (!identity) return false;
    if (Array.isArray(identity)) return identity.length > 0;
    if (typeof identity === 'object') return Object.keys(identity).length > 0;
    return true;
  }

  function buildStage2SourceSignatures(stage1Data) {
    const data = stage1Data && typeof stage1Data === 'object' ? stage1Data : {};
    const galleryEntries = Array.isArray(data.gallery_entries) ? data.gallery_entries : [];
    const features = Array.isArray(data.product_callouts) && data.product_callouts.length
      ? data.product_callouts
      : Array.isArray(data.features) && data.features.length
      ? data.features
      : Array.isArray(data.bullets)
      ? data.bullets
      : [];
    const assets = {
      brand_logo: pickAssetIdentity(data.brand_logo),
      scenario_asset: pickAssetIdentity(data.scenario_asset),
      product_image_1: pickAssetIdentity(data.product_image_1 || data.product_asset),
      product_image_2: pickAssetIdentity(data.product_image_2),
      gallery_entries: galleryEntries.map((entry) => ({
        asset: pickAssetIdentity(entry?.asset),
        caption: normalizeText(entry?.caption),
        title: normalizeText(entry?.title),
        subtitle: normalizeText(entry?.subtitle),
      })),
    };
    const copy = {
      brand_name: normalizeText(data.brand_name),
      agent_name: normalizeText(data.agent_name),
      title: normalizeText(data.title),
      subtitle: normalizeText(data.subtitle || data.tagline || data.promo),
      scenario_prompt: normalizeText(data.scenario_prompt),
      intent: normalizeText(data.intent),
      features: features.map((entry) => normalizeText(entry)).filter(Boolean),
    };
    const assetSignatures = {
      logo_source_signature: stableStringify(assets.brand_logo),
      scenario_source_signature: stableStringify(assets.scenario_asset),
      product_source_signature: stableStringify(assets.product_image_1),
      product_secondary_source_signature: stableStringify(assets.product_image_2),
      detected_gallery_assets_signature: stableStringify(
        assets.gallery_entries
          .map((entry) => entry.asset)
          .filter((entry) => entry != null && entry !== '')
      ),
    };
    return {
      assets,
      copy,
      assetSignatures,
      assetSignature: stableStringify(assets),
      copySignature: stableStringify(copy),
    };
  }

  function countStage1GalleryAssets(stage1Data) {
    const data = stage1Data && typeof stage1Data === 'object' ? stage1Data : {};
    const galleryEntries = Array.isArray(data.gallery_entries) ? data.gallery_entries : [];
    return galleryEntries.filter((entry) => hasPickedAssetIdentity(entry?.asset)).slice(0, 4).length;
  }

  function buildStage2FormStateSignatures({
    stage1Data,
    bottomRequestState,
    copyOptimization,
    adjustments,
  } = {}) {
    const source = buildStage2SourceSignatures(stage1Data);
    const detectedGalleryCount = countStage1GalleryAssets(stage1Data);
    const bottom = {
      bottom_mode: bottomRequestState?.bottom_mode || null,
      gallery_mode: bottomRequestState?.gallery_mode || null,
      requested_gallery_count: detectedGalleryCount,
      gallery_input_count_raw: detectedGalleryCount,
      gallery_input_count_normalized: detectedGalleryCount,
      gallery_autofill_applied: false,
      auto_fill_gallery: false,
      requested_title_text: normalizeText(bottomRequestState?.requested_title_text),
      requested_subtitle_text: normalizeText(bottomRequestState?.requested_subtitle_text),
    };
    const acceptedFeatures = Array.isArray(copyOptimization?.acceptedFeatures)
      ? copyOptimization.acceptedFeatures
      : Array.isArray(copyOptimization?.accepted_features)
      ? copyOptimization.accepted_features
      : [];
    const copyReviewAcceptance = {
      mode: copyOptimization?.mode || 'off',
      decision: copyOptimization?.decision || 'pending',
      accepted_title: normalizeText(copyOptimization?.acceptedTitle || copyOptimization?.accepted_title),
      accepted_subtitle: normalizeText(copyOptimization?.acceptedSubtitle || copyOptimization?.accepted_subtitle),
      accepted_features: acceptedFeatures.map((entry) => normalizeText(entry)).filter(Boolean).slice(0, 4),
    };
    const requestControls = {
      show_bullets: adjustments?.showBullets !== false,
      title_size: adjustments?.titleSize || null,
      quality_mode: adjustments?.qualityMode || null,
    };
    return {
      ...source,
      bottom,
      copyReviewAcceptance,
      requestControls,
      canonicalForm: {
        bottom_mode: bottom.bottom_mode,
        gallery_mode: bottom.gallery_mode,
        detected_gallery_items: detectedGalleryCount,
        detected_gallery_assets_signature: source.assetSignatures.detected_gallery_assets_signature,
        title_text: source.copy.title,
        subtitle_text: source.copy.subtitle,
        callouts_text: source.copy.features,
        logo_source_signature: source.assetSignatures.logo_source_signature,
        scenario_source_signature: source.assetSignatures.scenario_source_signature,
        product_source_signature: source.assetSignatures.product_source_signature,
        product_secondary_source_signature: source.assetSignatures.product_secondary_source_signature,
        copy_optimization_mode: copyReviewAcceptance.mode,
        copy_optimization_decision: copyReviewAcceptance.decision,
        copy_optimization_accepted_title: copyReviewAcceptance.accepted_title,
        copy_optimization_accepted_subtitle: copyReviewAcceptance.accepted_subtitle,
        copy_optimization_accepted_features: copyReviewAcceptance.accepted_features,
      },
      bottomSignature: stableStringify(bottom),
      copyReviewAcceptanceSignature: stableStringify(copyReviewAcceptance),
      requestControlsSignature: stableStringify(requestControls),
      formSignature: stableStringify({
        assets: source.assets,
        copy: source.copy,
        bottom,
        copyReviewAcceptance,
        requestControls,
      }),
    };
  }

  function diffStage2FormSignatures(previous, next) {
    if (!previous || !next) return [];
    const changed = [];
    if (previous.assetSignature !== next.assetSignature) changed.push('assets');
    if (previous.copySignature !== next.copySignature) changed.push('copy');
    if (previous.bottomSignature !== next.bottomSignature) changed.push('bottom_contract');
    if (previous.copyReviewAcceptanceSignature !== next.copyReviewAcceptanceSignature) {
      changed.push('copy_optimization_acceptance');
    }
    if (previous.requestControlsSignature !== next.requestControlsSignature) changed.push('request_controls');
    return changed;
  }

  function buildStage2PreflightDiagnostics({
    requestId,
    formSignatures,
    payload,
    previousSuccessPresent,
    invalidatedFields,
    clearedSuccessState,
    detectedGalleryItems,
  } = {}) {
    return {
      request_id: requestId ?? null,
      current_bottom_mode: formSignatures?.bottom?.bottom_mode || null,
      previous_success_present: Boolean(previousSuccessPresent),
      invalidated_fields: Array.isArray(invalidatedFields) ? invalidatedFields : [],
      cleared_success_state: Boolean(clearedSuccessState),
      detected_gallery_items: Number(detectedGalleryItems || 0),
      canonical_form_signature: formSignatures?.formSignature || '',
      canonical_form_signature_hash: hashStableValue(formSignatures?.formSignature || ''),
      request_payload_signature: stableStringify(payload || {}),
      request_payload_signature_hash: hashStableValue(payload || {}),
    };
  }

  function buildPoster2PayloadFromNormalisedInputs(input) {
    const galleryImages = Array.isArray(input.galleryImages) ? input.galleryImages : [];
    const galleryImageCount = galleryImages.length;
    const copyOptimization = input.copyOptimization || {};
    const acceptedFeatures = Array.isArray(copyOptimization.accepted_features)
      ? copyOptimization.accepted_features
      : Array.isArray(copyOptimization.acceptedFeatures)
      ? copyOptimization.acceptedFeatures
      : [];
    return {
      template_id: input.templateId,
      renderer_mode: input.rendererMode || 'auto',
      brand_name: input.brandName || '',
      agent_name: input.agentName || '',
      title: input.title || '',
      subtitle: input.subtitle || '',
      features: Array.isArray(input.features) ? input.features.slice(0, 4) : [],
      product_image: input.productImage || { url: '', key: null },
      product_secondary_image: input.productSecondaryImage || null,
      logo: input.logo || null,
      scenario_image: input.scenarioImage || null,
      gallery_images: galleryImages.map((entry) => ({
        url: entry.url || '',
        key: entry.key || null,
        caption: entry.caption || null,
      })),
      gallery_input_count_raw: galleryImageCount,
      gallery_input_count_normalized: galleryImageCount,
      gallery_requested_count: galleryImageCount,
      gallery_autofill_applied: false,
      bottom_mode: input.bottomRequestState?.bottom_mode || 'title_gallery_split',
      gallery_mode: input.bottomRequestState?.gallery_mode || 'strip_local_visible_only',
      style: {
        prompt: input.stylePrompt || '',
      },
      copy_optimization: {
        mode: copyOptimization.mode || 'off',
        decision: copyOptimization.decision || 'pending',
        accepted_title: copyOptimization.accepted_title || copyOptimization.acceptedTitle || '',
        accepted_subtitle: copyOptimization.accepted_subtitle || copyOptimization.acceptedSubtitle || '',
        accepted_features: acceptedFeatures.filter(Boolean).slice(0, 4),
      },
    };
  }

  function buildGeneratePosterPayloadFromForm(formState) {
    const snapshot = cloneValue(formState || {});
    return buildPoster2PayloadFromNormalisedInputs(snapshot);
  }

  function buildPoster2RequestSummary(payload) {
    return {
      template_id: payload?.template_id || null,
      renderer_mode: payload?.renderer_mode || null,
      bottom_mode: payload?.bottom_mode || null,
      gallery_mode: payload?.gallery_mode || null,
      title: payload?.title || '',
      subtitle: payload?.subtitle || '',
      feature_count: Array.isArray(payload?.features) ? payload.features.length : 0,
      gallery_count: Array.isArray(payload?.gallery_images) ? payload.gallery_images.length : 0,
      logo_url: payload?.logo?.url || null,
      scenario_url: payload?.scenario_image?.url || null,
      product_url: payload?.product_image?.url || null,
      gallery_urls: Array.isArray(payload?.gallery_images)
        ? payload.gallery_images.map((entry) => entry?.url || null)
        : [],
      copy_optimization_decision: payload?.copy_optimization?.decision || 'pending',
    };
  }

  function containsFamilyAFryerSignal(text) {
    const value = normalizeText(text).toLowerCase();
    if (!value) return false;
    return [
      'fryer',
      'fry station',
      'thermostat',
      'stainless steel',
      'fast heat',
      'fast heating',
    ].some((signal) => value.includes(signal));
  }

  function isFamilyACommercialFryerVariant({
    titleText,
    subtitleText,
    agentName,
    featureTexts,
  } = {}) {
    if (containsFamilyAFryerSignal(titleText) || containsFamilyAFryerSignal(subtitleText)) {
      return true;
    }
    if (containsFamilyAFryerSignal(agentName)) {
      return true;
    }
    return Array.isArray(featureTexts) && featureTexts.some((entry) => containsFamilyAFryerSignal(entry));
  }

  function resolveTemplateAPreviewTruth({
    titleText,
    subtitleText,
    agentName,
    featureTexts,
    hasSecondaryAsset,
    galleryCount,
    bottomMode,
    galleryMode,
    latestResult,
  } = {}) {
    const templateBehavior = latestResult?.template_behavior || {};
    const productPolicy = templateBehavior?.product_policy || {};
    const bottomReview = latestResult?.bottom_contract_review || {};
    const fryerVariant = isFamilyACommercialFryerVariant({
      titleText,
      subtitleText,
      agentName,
      featureTexts,
    });
    const resolvedBottomMode =
      bottomReview?.effective_bottom_mode ||
      bottomReview?.bottom_mode ||
      bottomMode ||
      'title_gallery_split';
    const resolvedGalleryMode =
      bottomReview?.gallery_mode ||
      galleryMode ||
      'strip_local_visible_only';
    const productGeometryMode =
      productPolicy?.product_geometry_mode ||
      (fryerVariant
        ? hasSecondaryAsset
          ? 'family_a_fryer_hero_supporting_inset_v1'
          : 'family_a_fryer_hero_stage_v1'
        : hasSecondaryAsset
        ? 'primary_secondary_dual_v2'
        : 'single_primary_v1');
    const showSecondaryInset =
      typeof productPolicy?.product_secondary_slot_rendered === 'boolean'
        ? productPolicy.product_secondary_slot_rendered
        : Boolean(fryerVariant && hasSecondaryAsset);
    return {
      headerMode: 'identity_left_agent_right',
      featureMode: 'product_anchor_callouts',
      annotationOwner: 'product_region',
      bottomMode: resolvedBottomMode,
      galleryMode: resolvedGalleryMode,
      footerOrdering: 'title_subtitle_above_gallery',
      productComposition: showSecondaryInset ? 'single_primary_supporting_inset' : 'single_primary',
      productGeometryMode,
      fryerVariant,
      showSecondaryInset,
      subtitleVisible: resolvedBottomMode !== 'gallery_only' && Boolean(normalizeText(subtitleText)),
      galleryVisible: resolvedBottomMode !== 'text_only_expanded' && Number(galleryCount || 0) > 0,
    };
  }

  function diffPayloadPaths(before, after, prefix = '') {
    if (stableStringify(before) === stableStringify(after)) return [];
    const currentPath = prefix || '$';
    const beforeIsArray = Array.isArray(before);
    const afterIsArray = Array.isArray(after);
    if (beforeIsArray || afterIsArray) {
      const maxLength = Math.max(beforeIsArray ? before.length : 0, afterIsArray ? after.length : 0);
      const diff = [];
      for (let index = 0; index < maxLength; index += 1) {
        diff.push(...diffPayloadPaths(before?.[index], after?.[index], `${currentPath}[${index}]`));
      }
      return diff;
    }
    const beforeIsObject = before && typeof before === 'object';
    const afterIsObject = after && typeof after === 'object';
    if (beforeIsObject || afterIsObject) {
      const keys = new Set([
        ...Object.keys(beforeIsObject ? before : {}),
        ...Object.keys(afterIsObject ? after : {}),
      ]);
      const diff = [];
      Array.from(keys).sort().forEach((key) => {
        diff.push(...diffPayloadPaths(before?.[key], after?.[key], `${currentPath}.${key}`));
      });
      return diff;
    }
    return [currentPath];
  }

  function createRequestCoordinator() {
    let activeId = 0;
    return {
      start() {
        activeId += 1;
        return activeId;
      },
      isCurrent(requestId) {
        return requestId === activeId;
      },
      active() {
        return activeId;
      },
    };
  }

  const api = {
    cloneValue,
    stableStringify,
    hashStableValue,
    pickAssetIdentity,
    countStage1GalleryAssets,
    buildStage2SourceSignatures,
    buildStage2FormStateSignatures,
    diffStage2FormSignatures,
    buildStage2PreflightDiagnostics,
    buildGeneratePosterPayloadFromForm,
    buildPoster2PayloadFromNormalisedInputs,
    buildPoster2RequestSummary,
    containsFamilyAFryerSignal,
    isFamilyACommercialFryerVariant,
    resolveTemplateAPreviewTruth,
    diffPayloadPaths,
    createRequestCoordinator,
  };

  globalScope.Stage2RequestHelpers = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : window);
