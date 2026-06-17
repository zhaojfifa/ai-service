/* CUISTANCE Email Campaign Composite — narrow operator flow (additive, isolated).
 * Sends template_id=email_campaign_composite_v1 + renderer_mode=puppeteer DIRECTLY to
 * /api/v2/generate-poster (it never passes through resolvePoster2PilotTemplateId /
 * resolvePoster2CompositionTemplateId, so it can never be remapped to template_dual_v2).
 *
 * ASSET PATH: each selected file is uploaded to R2 via /api/r2/presign-put + a presigned PUT (the same
 * mechanism main Stage1/2 uses). The generate payload then carries ONLY {url, key} — never a data: URL /
 * base64 (the BodyGuard rejects inline base64 by design). If R2 is not configured / upload fails, the page
 * shows "R2 upload unavailable" and DOES NOT call generate-poster (never sends base64).
 * No AI calls here; no real email send (send is Owner-gated / disabled). */
(function () {
  'use strict';

  // operator MVP fallback defaults (case001), used inline (no remote JSON fetch -> no 404 noise).
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
  function setStatus(t) { $('status').textContent = t; }

  function prefill(d, src) {
    $('brand_name').value = d.brand_name; $('series_name').value = d.series_name;
    $('title').value = d.title; $('strapline').value = d.strapline;
    $('product_ref').value = d.product_ref; $('spec_strip').value = d.spec_strip;
    $('callout1').value = d.callouts[0]; $('callout2').value = d.callouts[1]; $('callout3').value = d.callouts[2];
    $('contact_email').value = d.contact_email; $('contact_phone').value = d.contact_phone; $('contact_web').value = d.contact_web;
    $('pack-src').textContent = src;
  }

  // load pack = (re)apply the inline case001 copy defaults. Asset files are still uploaded by the operator.
  function loadPack() {
    prefill(CASE001, '已载入 case001 文案默认值（素材仍需上传；上传将走 R2 presign，不发 base64）');
  }

  function pickFile(id) { var i = $(id); return (i && i.files && i.files[0]) || null; }

  // R2 presign + PUT (mirrors main app.js r2PresignPut). Returns {url, key} (no base64). Throws on failure.
  async function r2UploadFile(folder, file) {
    var pres = await fetch('/api/r2/presign-put', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder: folder || 'uploads', filename: file.name || 'upload.bin',
        content_type: file.type || 'image/png', size: (typeof file.size === 'number' ? file.size : null)
      })
    });
    if (!pres.ok) {
      var et = await pres.text().catch(function () { return ''; });
      throw new Error('presign HTTP ' + pres.status + ' ' + et.slice(0, 140));
    }
    var d = await pres.json();
    if (!d || !d.key || !d.put_url) throw new Error('presign 响应缺少 key/put_url');
    var put = await fetch(d.put_url, { method: 'PUT', headers: { 'Content-Type': file.type || 'image/png' }, body: file });
    if (!put.ok) { throw new Error('R2 PUT HTTP ' + put.status); }
    var httpUrl = d.get_url || d.public_url || null;          // prefer HTTPS readable URL
    var ref = { url: httpUrl || d.r2_url || '', key: d.key };  // r2://key fallback; key always carried
    if (!ref.url) throw new Error('R2 未返回可读取的 url（缺 get_url/public_url/r2_url）');
    return ref;
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
    // 1) preflight — product hero is required; empty -> block, do NOT call generate-poster
    var productFile = pickFile('f_product');
    if (!productFile) { setStatus('请先上传「产品主图 Product hero」后再生成（preflight 已阻止，未调用生成接口）。'); return; }

    // 2) upload each provided asset to R2 (presign + PUT). On any failure -> stop, never send base64.
    var refs;
    try {
      setStatus('上传素材到 R2（presign + PUT）…');
      refs = { product: await r2UploadFile('product', productFile) };
      var lf = pickFile('f_logo'); refs.logo = lf ? await r2UploadFile('logo', lf) : null;
      var af = pickFile('f_atmo'); refs.atmo = af ? await r2UploadFile('scenario', af) : null;
      refs.gallery = [];
      var gids = ['f_g1', 'f_g2', 'f_g3'];
      for (var i = 0; i < gids.length; i++) {
        var gf = pickFile(gids[i]);
        if (gf) refs.gallery.push(await r2UploadFile('gallery', gf));
      }
    } catch (e) {
      window.__lastUploadError = String(e);
      setStatus('R2 upload unavailable / R2 上传不可用：' + e + ' — 已停止，未向生成接口发送任何 base64。');
      return; // hard stop — never fall back to base64
    }

    // 3) build payload with url/key ONLY (no data:/base64)
    var payload = {
      template_id: 'email_campaign_composite_v1',
      renderer_mode: 'puppeteer',
      brand_name: $('brand_name').value,
      agent_name: $('brand_name').value,
      title: $('title').value,
      subtitle: $('strapline').value,
      features: [$('callout1').value, $('callout2').value, $('callout3').value].filter(Boolean),
      product_image: { url: refs.product.url, key: refs.product.key },
      logo: refs.logo ? { url: refs.logo.url, key: refs.logo.key } : null,
      scenario_image: refs.atmo ? { url: refs.atmo.url, key: refs.atmo.key } : null,
      gallery_images: refs.gallery.map(function (r) { return { url: r.url, key: r.key, caption: null }; })
    };
    // safety assertion: no base64/data: in the outgoing payload
    var bodyStr = JSON.stringify(payload);
    if (/data:image|;base64,/.test(bodyStr)) {
      setStatus('内部错误：payload 仍含 base64，已阻止发送。'); return;
    }
    window.__lastRequestSummary = {
      template_id: payload.template_id, renderer_mode: payload.renderer_mode,
      brand_name: payload.brand_name, title: payload.title, subtitle: payload.subtitle, features: payload.features,
      product_image: payload.product_image, logo: payload.logo, scenario_image: payload.scenario_image,
      gallery_images: payload.gallery_images,
      payload_contains_base64: /data:image|;base64,/.test(bodyStr)
    };

    setStatus('生成中…（调用 /api/v2/generate-poster · email_campaign_composite_v1）');
    try {
      var resp = await fetch('/api/v2/generate-poster', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: bodyStr
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
    prefill(CASE001, '（默认 case001 文案已就绪；上传素材将通过 R2 presign 上传，仅传 url/key）');
  });
})();
