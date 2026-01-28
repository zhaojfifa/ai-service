/* Mode S Stage1 Adapter
 * Goal: make Mode S layout work on top of existing app.js without touching backend.
 * Must:
 *  - Always log when executed (so we can prove it runs)
 *  - Fetch templates/registry.json (Pages-relative via App.utils.assetUrl)
 *  - Bind local file previews via objectURL using data-inline-preview + input[name]
 *  - Never white-screen even if something is missing
 */
(function () {
  // HARD TRACE (must appear in console if script loads)
  console.log("[ModeS] adapter loaded", window.location.href);

  const body = document.body;
  const isStage1 = body && (body.dataset.stage === "stage1" || body.dataset.page === "stage1");
  if (!isStage1) {
    console.log("[ModeS] adapter: not stage1, skip");
    return;
  }

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function safeOn(el, ev, fn) {
    if (!el) return console.warn(`[ModeS] missing node for ${ev}`);
    el.addEventListener(ev, fn);
  }

  // Use existing helper if available (kit1.2 app.js defines App.utils.assetUrl)
  const assetUrl = (rel) => {
    if (window.App?.utils?.assetUrl) return window.App.utils.assetUrl(rel);
    return new URL(rel, document.baseURI).toString();
  };

  function uncloak() {
    // If any CSS/placeholder hides the page, undo it.
    document.documentElement.classList.remove("cloak");
    document.body.classList.remove("cloak");
    document.body.style.visibility = "visible";
    document.body.style.opacity = "1";
  }

  function bindInlinePreviews() {
    const inputs = $$('input[type="file"][name]');
    for (const input of inputs) {
      const name = input.getAttribute("name");
      const img = $(`img[data-inline-preview="${name}"]`);
      if (!img) continue;

      let lastUrl = null;
      safeOn(input, "change", () => {
        const f = input.files?.[0];
        if (!f) return;
        if (lastUrl) URL.revokeObjectURL(lastUrl);
        lastUrl = URL.createObjectURL(f);
        img.src = lastUrl;
        img.style.visibility = "visible";
      });
    }
  }

  async function loadRegistryIntoSelect() {
    // Prefer Mode S select by name first; fallback to legacy ids
    const sel =
      $('select[name="template_id"]') ||
      $("#template-select") ||
      $("#templateSelect") ||
      $("#template-select-stage1");

    if (!sel) {
      console.warn("[ModeS] template select not found; cannot load registry");
      return;
    }

    const url = assetUrl("templates/registry.json");
    console.log("[ModeS] fetching registry:", url);

    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`registry fetch failed: ${res.status} ${url}`);
    const reg = await res.json();

    const list = Array.isArray(reg) ? reg : (reg.templates || reg.items || []);
    sel.innerHTML = "";

    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "请选择模板";
    sel.appendChild(opt0);

    for (const t of list) {
      const opt = document.createElement("option");
      opt.value = t.id || t.key || t.name;
      opt.textContent = t.title || t.name || t.id;
      opt.dataset.spec = t.spec || t.spec_path || t.specUrl || "";
      sel.appendChild(opt);
    }

    safeOn(sel, "change", async () => {
      await loadSpecForSelected(sel);
    });
  }

  async function loadSpecForSelected(sel) {
    const opt = sel.selectedOptions?.[0];
    if (!opt || !opt.value) return;

    // Spec path from registry if present; else default naming
    const specPath = opt.dataset.spec || `templates/${opt.value}_spec.json`;
    const url = assetUrl(specPath);
    console.log("[ModeS] fetching spec:", url);

    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`spec fetch failed: ${res.status} ${url}`);
    const spec = await res.json();

    // Fill description (optional)
    const desc =
      $("#template-description") ||
      $("#template-description-stage1") ||
      $("[data-template-description]");
    if (desc) desc.textContent = spec.description || spec.title || "";

    // Preview (optional hook)
    const canvas =
      $("#template-preview") ||
      $("#template-preview-stage1") ||
      $("#template-preview-canvas");
    if (canvas && window.App?.renderers?.renderTemplatePreview) {
      window.App.renderers.renderTemplatePreview(canvas, spec);
    }
  }

  (async function boot() {
    try {
      uncloak();
      bindInlinePreviews();
      await loadRegistryIntoSelect();
      console.log("[ModeS] adapter ready");
    } catch (e) {
      console.error("[ModeS] adapter failed", e);
      uncloak(); // never leave blank screen
    }
  })();
})();