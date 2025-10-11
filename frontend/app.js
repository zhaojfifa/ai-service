/* app.js — 前端主逻辑（可直接替换）
 * 依赖：placeholder.js（已导出 resolveApiBases / warmUp / pickHealthyBase / postJsonWithRetry）
 */
(() => {
  'use strict';

  // ---------------------------
  // 小工具
  // ---------------------------
  const STORAGE_KEYS = { apiBase: 'mkt.apiBase' };

  function $(sel, root = document) { return root.querySelector(sel); }
  function $all(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

  function setStatus(el, text, level = 'info') {
    if (!el) return;
    el.textContent = String(text || '');
    el.dataset.level = level; // 你的样式里可用 [data-level="error"] 定义颜色
  }

  function clampVariants(v) {
    const n = Number(v ?? 1);
    return Math.min(8, Math.max(1, isFinite(n) ? Math.round(n) : 1));
  }

  function validatePayloadSize(raw) {
    const limit = 350_000; // ~350KB，上限可按需调
    if (raw.length > limit) {
      throw new Error(`请求体过大（${(raw.length/1024).toFixed(1)} KB），请确认图片已直传，仅传 key/url。`);
    }
  }

  // 保守的“资产就绪”处理（占位：不主动上传，只保持字段规范）
  async function hydrateStage1DataAssets(stage1) {
    // 此处只确保结构存在；具体直传/签名逻辑在其它模块完成
    stage1.brand_logo = stage1.brand_logo || null;
    stage1.scenario_asset = stage1.scenario_asset || null;
    stage1.product_asset  = stage1.product_asset  || null;
    return stage1;
  }

  // 收集候选 API 基址（input + data-* + window.APP_API_BASES）
  function getApiCandidates(extra = null) {
    const candidates = new Set();

    const inputVal = ($('#api-base')?.value || '').trim();
    if (inputVal) candidates.add(inputVal);

    const stored = localStorage.getItem(STORAGE_KEYS.apiBase) || '';
    if (stored) candidates.add(stored);

    const bodydata = document.body?.dataset ?? {};
    [bodydata.workerBase, bodydata.renderBase, bodydata.apiBase, window.APP_DEFAULT_API_BASE]
      .filter(Boolean).forEach(v => candidates.add(String(v)));

    if (Array.isArray(window.APP_API_BASES)) {
      window.APP_API_BASES.forEach(v => candidates.add(String(v)));
    }

    if (extra) {
      (Array.isArray(extra) ? extra : String(extra).split(','))
        .map(s => s && String(s).trim()).filter(Boolean)
        .forEach(v => candidates.add(v));
    }

    const list = Array.from(candidates);
    try { return (window.resolveApiBases ? window.resolveApiBases(list) : list); }
    catch { return list; }
  }

  // 把任何“对象形态”的 prompt 规范成字符串
  function toPromptString(x) {
    if (x == null) return '';
    if (typeof x === 'string') return x.trim();
    if (typeof x.text === 'string')   return x.text.trim();
    if (typeof x.prompt === 'string') return x.prompt.trim();
    if (x.preset && x.aspect) return `${x.preset} (aspect ${x.aspect})`;
    if (x.preset)             return String(x.preset);
    try { return JSON.stringify(x); } catch { return String(x); }
  }

  // ---------------------------
  // 生成主流程（关键修复已在此）
  // ---------------------------
  async function triggerGeneration(options) {
    const {
      stage1Data,                        // 表单解析后的数据结构（品牌/产品/素材等）
      statusElement,                     // 状态提示节点
      layoutStructure,                   // 版式结构预览节点（可选）
      posterOutput, aiPreview, aiSpinner, aiPreviewMessage,
      posterVisual, posterImage, variantsStrip,
      promptGroup, emailGroup,          // 面板分组
      promptTextarea, emailTextarea,    // 文案显示区域
      generateButton, regenerateButton, nextButton,
      promptManager, updatePromptPanels, // Prompt Inspector 注入
      forceVariants = null, abTest = false,
    } = options || {};

    // 1) 基址候选
    const apiCandidates = getApiCandidates($('#api-base')?.value || null);
    if (!apiCandidates.length) {
      setStatus(statusElement, '未找到可用的后端地址，请先配置 Render / Worker。', 'warning');
      return null;
    }

    // 2) 资产结构补全
    await hydrateStage1DataAssets(stage1Data);

    // 3) 组装 Poster 主体（与后端字段对应）
    const scenarioAsset = stage1Data.scenario_asset || null;
    const productAsset  = stage1Data.product_asset  || null;

    const payload = {
      brand_name: stage1Data.brand_name,
      agent_name: stage1Data.agent_name,
      scenario_image: stage1Data.scenario_image,
      product_name: stage1Data.product_name,
      template_id: stage1Data.template_id || 'dual',
      features: stage1Data.features,
      title: stage1Data.title,
      subtitle: stage1Data.subtitle,
      series_description: stage1Data.series_description,

      brand_logo: stage1Data.brand_logo?.dataUrl || null,

      scenario_asset:
        scenarioAsset && scenarioAsset.r2Key ? null :
        (scenarioAsset?.dataUrl?.startsWith('data:') ? scenarioAsset.dataUrl : null),
      scenario_key: scenarioAsset?.r2Key || null,

      product_asset:
        productAsset && productAsset.r2Key ? null :
        (productAsset?.dataUrl?.startsWith('data:') ? productAsset.dataUrl : null),
      product_key: productAsset?.r2Key || null,

      scenario_mode:  stage1Data.scenario_mode || 'upload',
      scenario_prompt: (stage1Data.scenario_mode === 'prompt')
        ? (stage1Data.scenario_prompt || stage1Data.scenario_image)
        : null,

      product_mode: stage1Data.product_mode || 'upload',
      product_prompt: stage1Data.product_prompt || null,

      gallery_items: (stage1Data.gallery_entries || []).map((entry) => {
        const asset   = entry.asset || null;
        const dataUrl = asset?.dataUrl;
        const r2Key   = asset?.r2Key || null;
        const serialisedAsset = r2Key || !(typeof dataUrl === 'string' && dataUrl.startsWith('data:'))
          ? null
          : dataUrl;
        return {
          caption: entry.caption?.trim() || null,
          asset: serialisedAsset,
          key: r2Key,
          mode: entry.mode || 'upload',
          prompt: entry.prompt?.trim() || null,
        };
      }),
    };

    // 4) Prompt/Variants —— 这里把 prompts 统一转成“字符串”
    const promptConfig = (promptManager?.buildRequest?.() || {
      prompts: {}, variants: 1, seed: null, lockSeed: false,
    });
    if (forceVariants != null) promptConfig.variants = clampVariants(forceVariants);

    const bundleIn = promptConfig.prompts || {};
    const prompts = {
      scenario: toPromptString(bundleIn.scenario),
      product : toPromptString(bundleIn.product),
      gallery : toPromptString(bundleIn.gallery),
    };

    const requestPayload = {
      poster: payload,
      render_mode: 'locked',
      variants: promptConfig.variants,
      seed: promptConfig.seed,
      lock_seed: Boolean(promptConfig.lockSeed),
      prompts, // 👈 现在是字符串
    };

    // 更新可视化面板（如果接入了 Prompt Inspector）
    if (typeof updatePromptPanels === 'function') {
      updatePromptPanels({ bundle: prompts });
    }

    // 5) 体积校验
    const rawPayload = JSON.stringify(requestPayload);
    try { validatePayloadSize(rawPayload); }
    catch (e) { setStatus(statusElement, e.message, 'error'); return null; }

    // 6) UI 状态
    generateButton && (generateButton.disabled = true);
    regenerateButton && (regenerateButton.disabled = true);
    setStatus(statusElement, abTest ? '正在进行 A/B 提示词生成…' : '正在生成海报与营销文案…', 'info');
    posterOutput && posterOutput.classList.remove('hidden');
    aiPreview && aiPreview.classList.remove('complete');
    aiSpinner && aiSpinner.classList.remove('hidden');
    aiPreviewMessage && (aiPreviewMessage.textContent = 'Glibatree Art Designer 正在绘制海报…');
    posterVisual && posterVisual.classList.add('hidden');
    promptGroup && promptGroup.classList.add('hidden');
    emailGroup && emailGroup.classList.add('hidden');
    nextButton && (nextButton.disabled = true);
    if (variantsStrip) { variantsStrip.innerHTML = ''; variantsStrip.classList.add('hidden'); }

    // 7) 探活 + 发送（用 placeholder.js 的网络栈；传 rawPayload 确保用的是转换后的数据）
    try {
      await (window.warmUp?.(apiCandidates));
      const res = await window.postJsonWithRetry(apiCandidates, '/api/generate-poster', requestPayload, 2, rawPayload);
      const data = await res.json();

      // —— 根据你的后端返回渲染结果（保持宽松，避免空值报错）
      if (layoutStructure && data.layout_preview) {
        layoutStructure.textContent = data.layout_preview;
      }

      if (posterImage && data.poster_url) {
        posterImage.src = data.poster_url;
        posterVisual && posterVisual.classList.remove('hidden');
      }

      if (promptTextarea && data.prompts_text) {
        promptTextarea.value = data.prompts_text;
      }
      if (emailTextarea && data.email_text) {
        emailTextarea.value = data.email_text;
      }

      setStatus(statusElement, '已生成完成。', 'success');
      aiSpinner && aiSpinner.classList.add('hidden');
      aiPreview && aiPreview.classList.add('complete');
      nextButton && (nextButton.disabled = false);
      return data;
    } catch (err) {
      console.error(err);
      setStatus(statusElement, `生成失败：${err?.message || err}`, 'error');
      aiSpinner && aiSpinner.classList.add('hidden');
      nextButton && (nextButton.disabled = true);
      throw err;
    } finally {
      generateButton && (generateButton.disabled = false);
      regenerateButton && (regenerateButton.disabled = false);
    }
  }

  // ---------------------------
  // 对外导出（与旧版保持同名）
  // ---------------------------
  window.getApiCandidates   = getApiCandidates;
  window.triggerGeneration  = triggerGeneration;

  // 便于其它模块复用
  window.__app_util__ = {
    setStatus, clampVariants, validatePayloadSize, toPromptString, hydrateStage1DataAssets,
  };
})();
