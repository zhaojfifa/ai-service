from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "scripts" / "sync_frontend_to_docs.sh"
CHECK_SCRIPT = ROOT / "scripts" / "check_frontend_docs_sync.sh"


def _write_asset_tree(
    base: Path,
    *,
    index: str = "index",
    stage2: str,
    app: str,
    styles: str,
    helpers: str = "window.stage2RequestHelpers = {};",
) -> None:
    frontend = base / "frontend"
    docs = base / "docs"
    frontend.mkdir()
    docs.mkdir()
    (frontend / "index.html").write_text(index, encoding="utf-8")
    (frontend / "stage2.html").write_text(stage2, encoding="utf-8")
    (frontend / "app.js").write_text(app, encoding="utf-8")
    (frontend / "styles.css").write_text(styles, encoding="utf-8")
    (frontend / "stage2_request_helpers.js").write_text(helpers, encoding="utf-8")
    (docs / "index.html").write_text(index, encoding="utf-8")
    (docs / "stage2.html").write_text(stage2, encoding="utf-8")
    (docs / "app.js").write_text(app, encoding="utf-8")
    (docs / "styles.css").write_text(styles, encoding="utf-8")
    (docs / "stage2_request_helpers.js").write_text(helpers, encoding="utf-8")


def _env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FRONTEND_DIR"] = str(tmp_path / "frontend")
    env["DOCS_DIR"] = str(tmp_path / "docs")
    return env


def test_check_frontend_docs_sync_detects_stale_publish_files(tmp_path: Path):
    _write_asset_tree(tmp_path, stage2="new stage2", app="console.log('new')", styles="body{color:red;}")
    (tmp_path / "docs" / "app.js").write_text("console.log('old')", encoding="utf-8")

    proc = subprocess.run(
        ["bash", str(CHECK_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "stale publish mirror: app.js" in proc.stderr


def test_sync_frontend_to_docs_restores_publish_mirror(tmp_path: Path):
    _write_asset_tree(tmp_path, stage2="new stage2", app="console.log('new')", styles="body{color:red;}")
    (tmp_path / "docs" / "stage2.html").write_text("old stage2", encoding="utf-8")

    subprocess.run(
        ["bash", str(SYNC_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["bash", str(CHECK_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=True,
    )

    assert (tmp_path / "docs" / "stage2.html").read_text(encoding="utf-8") == "new stage2"


def test_stage1_operator_surfaces_and_publish_mirror_are_aligned():
    root = ROOT
    frontend_index = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    docs_index = (root / "docs" / "index.html").read_text(encoding="utf-8")
    frontend_stage2 = (root / "frontend" / "stage2.html").read_text(encoding="utf-8")
    docs_stage2 = (root / "docs" / "stage2.html").read_text(encoding="utf-8")
    frontend_helpers = (root / "frontend" / "stage2_request_helpers.js").read_text(encoding="utf-8")
    docs_helpers = (root / "docs" / "stage2_request_helpers.js").read_text(encoding="utf-8")

    assert frontend_index == docs_index
    assert frontend_stage2 == docs_stage2
    assert frontend_helpers == docs_helpers
    assert "Bottom Support Copy" in frontend_index
    assert 'id="s1-core-assets" class="card stage-card" data-variant-visible="all"' in frontend_index
    assert 'id="stage1-product2-label"' in frontend_index
    assert "配件 / 刀头 / 材质辅图" in frontend_index
    assert "Product Series (optional)" in frontend_index
    assert "Product Callouts (optional, up to 3)" in frontend_index
    assert "Bottom Support" in frontend_index
    assert "data-secondary-image-clear" in frontend_index
    assert "preview-family-b" in frontend_index
    assert "preview-b-product-image" in frontend_index
    assert 'id="open-stage1-preview"' in frontend_index
    assert 'id="preview-container" class="preview hidden"' in frontend_index
    assert "Open Preview" in frontend_index
    assert frontend_index.index('id="s1-core-assets"') < frontend_index.index("Product Callouts (optional, up to 3)") < frontend_index.index('id="s1-bottom-thumbs"') < frontend_index.index("Bottom Support Copy (optional)")
    assert "Materials Evidence Strip" in frontend_stage2
    assert "Hero / Supporting Detail" in frontend_stage2
    assert "Product Callouts" in frontend_stage2
    assert "s2-template-b-summary" in frontend_stage2
    assert "s2-template-badge" in frontend_stage2
    assert 'id="poster2-detected-gallery-count"' in frontend_stage2
    assert "Detected gallery items" in frontend_stage2
    assert 'id="poster2-gallery-count"' not in frontend_stage2


def test_stage1_request_mapping_prefers_dedicated_product_callouts_and_secondary_clear_path_exists():
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function normaliseStage1ProductCallouts" in app_js
    assert "function resolveStage1ProductCallouts" in app_js
    assert "formData.getAll('product_callouts')" in app_js
    assert "product_callouts: productCallouts" in app_js
    assert "stage1Data.product_callouts" in app_js
    assert "state.productImage2 = null;" in app_js
    assert "input.value = '';" in app_js


def test_template_a_family_a_fryer_defaults_and_gallery_semantics_are_wired():
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "Electric Fryer Series" in app_js
    assert "Power Up Your Fry Station" in app_js
    assert "Fast heating, precise control, and durable stainless steel construction for everyday commercial use." in app_js
    assert "Fast Heating" in app_js
    assert "Precise Temperature Control" in app_js
    assert "Easy-Clean Stainless Steel" in app_js
    assert "Basket Detail" in app_js
    assert "Single Tank" in app_js
    assert "Lid Detail" in app_js
    assert "Dual Tank" in app_js
    assert app_js.index("Basket Detail") < app_js.index("Single Tank") < app_js.index("Lid Detail") < app_js.index("Dual Tank")
    assert "function buildModeSDefaultGalleryEntries" in app_js
    assert "function buildModeSFamilyAGalleryFallbackPlan" in app_js
    assert "function resolveModeSAgentName" in app_js
    assert "function isModeSGenericAgentText" in app_js
    assert "function countStage1GalleryAssets" in app_js
    assert "gallery_input_count_raw: detectedGalleryCount" in app_js
    assert "requested_gallery_count: detectedGalleryCount" in app_js
    assert "Detected gallery items:" in app_js


def test_template_a_preview_parity_uses_shared_helpers_and_supporting_inset():
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    stage2_html = (ROOT / "frontend" / "stage2.html").read_text(encoding="utf-8")
    helpers_js = (ROOT / "frontend" / "stage2_request_helpers.js").read_text(encoding="utf-8")

    assert "function buildTemplateAPreviewModel" in app_js
    assert "function applyTemplateAPreviewModel" in app_js
    assert "resolveTemplateAPreviewTruthLocal" in app_js
    assert 'id="preview-product-secondary-wrap"' in index_html
    assert 'id="poster-result-product-secondary-wrap"' in stage2_html
    assert 'id="preview-gallery" class="poster-gallery"' in index_html
    assert 'id="poster-result-gallery" class="poster-gallery"' in stage2_html
    assert 'src="./stage2_request_helpers.js' in index_html
    assert 'src="./stage2_request_helpers.js' in stage2_html
    assert "function resolveTemplateAPreviewTruth" in helpers_js


def test_template_b_independent_preview_and_generate_path_are_present():
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function buildTemplateBStage2State" in app_js
    assert "function buildTemplateBPosterPayload" in app_js
    assert "Template B / Family B summary" in app_js
    assert "endpointPath = '/api/v2/generate-poster';" in app_js
    assert "gallery: (posterPayload.gallery_items || []).map" in app_js
    assert "const rendererMode = stage2State.poster2.rendererMode || 'auto';" in app_js
    assert "puppeteerOption.disabled" not in app_js


def test_poster2_readme_indexes_family_isolation_rules():
    readme = (ROOT / "docs" / "poster2" / "README.md").read_text(encoding="utf-8")
    rules_doc = (ROOT / "docs" / "poster2" / "02_architecture" / "family_isolation_rules_v1.md").read_text(encoding="utf-8")
    rebaseline_doc = (ROOT / "docs" / "poster2" / "05_validation" / "template_a_isolation_rebaseline_status_v1.md").read_text(encoding="utf-8")

    assert "family_isolation_rules_v1.md" in readme
    assert "template_a_isolation_rebaseline_status_v1.md" in readme
    assert "one family, one evidence schema" in rules_doc
    assert "one family, one render material builder" in rules_doc
    assert "Canonical Family A runtime smoke" in rebaseline_doc
