/* CUISTANCE Email Campaign Composite — narrow operator flow (additive, isolated).
 * Sends template_id=email_campaign_composite_v1 + renderer_mode=puppeteer DIRECTLY to
 * /api/v2/generate-poster (it never passes through resolvePoster2PilotTemplateId /
 * resolvePoster2CompositionTemplateId, so it can never be remapped to template_dual_v2).
 * No AI calls here; no real email send (send is Owner-gated / disabled). */
(function () {
  'use strict';

  // operator MVP fallback defaults (case001). The page first TRIES to fetch the repo-local
  // ops_manual_test_pack_v1/input_fields_case001.json; if the browser cannot read it, these inline
  // defaults are used (documented as operator MVP fallback in the report).
  var CASE001 = {
    brand_name: 'CUISTANCE',
    series_name: 'Electric Fryer Series',
    title: 'LES FRITEUSES ÉLECTRIQUES',
    strapline: 'CUISSON PROFESSIONNELLE, CROUSTILLANT MAÎTRISÉ',
    product_ref: 'EF132V',
    spec_strip: 'RÉF. EF132V · 2 cuves 13 + 13 L · 3 + 3 kW / 230 V · L630 × P520 × H345 mm',
    callouts: ['2 cuves inox amovibles', "Thermostat réglable jusqu'à 190°C", 'Construction inox / usage professionnel'],
    contact_email: 'commercial@cuistance.eu',
    contact_phone: '+33 (0)1 71 84 11 20',
    contact_web: 'cuistance-europe.com'
  };

  var $ = function (id) { return document.getElementById(id); };
  var state = { posterKey: null };
  // Asset-by-URL mode for runtime smoke / R2-backed prod: when window.OPS_TEST_ASSET_BASE is set, "load
  // pack" fills these URLs and generate sends them (the backend fetches by URL, mirroring R2). Production
  // operators normally upload files; the inline-base64 request guard means real prod must upload to R2
  // first and send url/key (existing Stage2 mechanism). __opsAssetUrls stays empty unless test base is set.
  var __opsAssetUrls = {};
  function setStatus(t) { $('status').textContent = t; }

  function prefill(d, src) {
    $('brand_name').value = d.brand_name; $('series_name').value = d.series_name;
    $('title').value = d.title; $('strapline').value = d.strapline;
    $('product_ref').value = d.product_ref; $('spec_strip').value = d.spec_strip;
    $('callout1').value = d.callouts[0]; $('callout2').value = d.callouts[1]; $('callout3').value = d.callouts[2];
    $('contact_email').value = d.contact_email; $('contact_phone').value = d.contact_phone; $('contact_web').value = d.contact_web;
    $('pack-src').textContent = src;
  }

  async function loadPack() {
    // try repo-local JSON first; fall back to inline defaults
    try {
      var r = await fetch('assets/sop_source_materialization_v1/../ops_manual_test_pack_v1/input_fields_case001.json');
    } catch (e) { r = null; }
    var tryPaths = [
      'docs/poster2/assets/ops_manual_test_pack_v1/input_fields_case001.json',
      '../docs/poster2/assets/ops_manual_test_pack_v1/input_fields_case001.json'
    ];
    for (var i = 0; i < tryPaths.length; i++) {
      try {
        var resp = await fetch(tryPaths[i]);
        if (resp && resp.ok) {
          var j = await resp.json();
          prefill({
            brand_name: j.brand_name, series_name: 'Electric Fryer Series', title: j.title,
            strapline: j.subtitle, product_ref: j.product_ref, spec_strip: j.spec_strip,
            callouts: j.callouts, contact_email: j.contact.email, contact_phone: j.contact.phone, contact_web: j.contact.website
          }, '已从 ops_manual_test_pack_v1/input_fields_case001.json 载入');
          return;
        }
      } catch (e) { /* continue */ }
    }
    prefill(CASE001, '已载入内置 case001 默认值（operator MVP fallback；浏览器无法读取 repo 本地 JSON）');
    maybeFillTestAssetUrls();
  }

  function maybeFillTestAssetUrls() {
    var base = window.OPS_TEST_ASSET_BASE;
    if (!base) return;
    __opsAssetUrls = {
      logo: base + '/brand_logo.jpg', product: base + '/product_hero_fryer.jpg',
      g1: base + '/gallery_01.jpg', g2: base + '/gallery_02.jpg', g3: base + '/gallery_03.jpg',
      atmo: base + '/atmosphere_substrate_fries_hero.png'
    };
    var hint = document.getElementById('pack-src');
    if (hint) hint.textContent += ' · 测试素材 URL 模式（后端按 URL 拉取，等价于 R2）';
  }

  function fileToDataUrl(input) {
    return new Promise(function (resolve) {
      var f = input.files && input.files[0];
      if (!f) { resolve(null); return; }
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = function () { resolve(null); };
      fr.readAsDataURL(f);
    });
  }

  function yn(ok) { return '<span class="badge ' + (ok ? 'b-ok">是' : 'b-bad">否') + '</span>'; }

  function renderContractReview(body) {
    var rev = (body && body.email_campaign_composite_contract_review) || {};
    var t = rev.business_truth || {};
    var rows = [
      ['模板路线', (body.template_id || '') + ' ' + (body.template_id === 'email_campaign_composite_v1' ? '<span class="badge b-ok">正确</span>' : '<span class="badge b-bad">错误</span>')],
      ['渲染引擎 (renderer/engine)', (body.render_engine_used || '-')],
      ['海报托管', (rev.poster_hosting === 'r2' ? 'R2 HTTPS' : ('内联 data URL（本地无 R2）'))],
      ['结构完整 (structure_complete)', yn(rev.structure_complete === true)],
      ['卖点数量 (callout_count)', String(rev.callout_count) + (rev.callout_count === 3 ? ' <span class="badge b-ok">3</span>' : ' <span class="badge b-bad">≠3</span>')],
      ['无错误品牌/燃气灶泄漏 (leakage_clean)', yn(t.leakage_clean === true)],
      ['温控为 190°C（非 0–200°C）', yn(t.thermostat_uses_unsupported_0_200C === false)],
      ['氛围图不作为产品事实', yn(t.ai_substrate_is_truth === false)],
      ['氛围图来源', (t.substrate_source || '-')]
    ];
    $('cr').innerHTML = rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('');
  }

  async function generate() {
    setStatus('生成中…（调用 /api/v2/generate-poster · email_campaign_composite_v1）');
    // In test/R2 URL mode (OPS_TEST_ASSET_BASE set) prefer the asset URL — the backend fetches it by URL,
    // avoiding the inline-base64 request guard. Otherwise prefer an uploaded file (data URL).
    async function assetUrl(inputId, slot) {
      if (window.OPS_TEST_ASSET_BASE && __opsAssetUrls[slot]) return __opsAssetUrls[slot];
      var d = await fileToDataUrl($(inputId));
      return d || __opsAssetUrls[slot] || null;
    }
    var product = await assetUrl('f_product', 'product');
    var logo = await assetUrl('f_logo', 'logo');
    var atmo = await assetUrl('f_atmo', 'atmo');
    var g1 = await assetUrl('f_g1', 'g1'), g2 = await assetUrl('f_g2', 'g2'), g3 = await assetUrl('f_g3', 'g3');
    var gallery = [g1, g2, g3].filter(Boolean).map(function (u) { return { url: u, key: null, caption: null }; });
    var payload = {
      template_id: 'email_campaign_composite_v1',
      renderer_mode: 'puppeteer',
      brand_name: $('brand_name').value,
      agent_name: $('brand_name').value,
      title: $('title').value,
      subtitle: $('strapline').value,
      features: [$('callout1').value, $('callout2').value, $('callout3').value].filter(Boolean),
      product_image: { url: product || '', key: null },
      logo: logo ? { url: logo, key: null } : null,
      scenario_image: atmo ? { url: atmo, key: null } : null,
      gallery_images: gallery
    };
    window.__lastRequestSummary = {
      template_id: payload.template_id, renderer_mode: payload.renderer_mode,
      brand_name: payload.brand_name, title: payload.title, subtitle: payload.subtitle,
      features: payload.features,
      has_logo: !!payload.logo, has_product: !!product, has_scenario: !!atmo, gallery_count: gallery.length
    };
    try {
      var resp = await fetch('/api/v2/generate-poster', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      var body = await resp.json();
      window.__lastResponse = body;
      if (!resp.ok) { setStatus('生成失败 HTTP ' + resp.status + '：' + JSON.stringify(body).slice(0, 200)); return; }
      $('poster').src = body.final_url || '';
      state.posterKey = body.poster_key || null;
      var hosted = (body.final_url || '').slice(0, 5) === 'data:' ? '内联 data URL' : (body.final_url || '').slice(0, 40);
      $('meta').innerHTML = 'template_id=<b>' + body.template_id + '</b> · engine=' + (body.render_engine_used || '-') +
        ' · poster_key=' + (state.posterKey || '-') + ' · URL=' + hosted;
      renderContractReview(body);
      $('preview').disabled = !state.posterKey;
      setStatus('生成完成。template_id=' + body.template_id + '（' + (body.template_id === 'email_campaign_composite_v1' ? '已走正确路线' : '路线错误!') + '）');
    } catch (e) {
      setStatus('生成请求异常：' + e);
    }
  }

  async function emailPreview() {
    if (!state.posterKey) { setStatus('无 poster_key，无法预览。'); return; }
    setStatus('生成邮件预览…');
    try {
      var resp = await fetch('/api/v2/email/preview', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ poster_key: state.posterKey })
      });
      var b = await resp.json();
      window.__lastPreview = { http: resp.status, subject: b.subject, generated_from: b.generated_from };
      if (!resp.ok) { $('mail-meta').textContent = '预览 blocker：HTTP ' + resp.status + ' ' + JSON.stringify(b).slice(0, 200); return; }
      $('mail-meta').innerHTML = '主题：<b>' + (b.subject || '') + '</b> · 来源：' + (b.generated_from || '-');
      $('mail-text').textContent = (b.text || '').slice(0, 600);
      var doc = $('mail').contentWindow.document; doc.open(); doc.write(b.html || ''); doc.close();
      setStatus('邮件预览完成（发送仍被 Owner 锁定）。');
    } catch (e) {
      $('mail-meta').textContent = '预览 blocker（异常）：' + e;
      setStatus('邮件预览失败。');
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('load-pack').addEventListener('click', loadPack);
    $('generate').addEventListener('click', generate);
    $('preview').addEventListener('click', emailPreview);
    // send stays disabled — Owner-gated
    prefill(CASE001, '（默认 case001 已就绪；点击“加载测试素材包”可从 repo JSON 刷新）');
  });
})();
