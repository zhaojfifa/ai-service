import base64
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _encode_png(color: tuple[int, int, int] = (255, 0, 0)) -> str:
    image = Image.new("RGB", (64, 64), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture()
def template_tmpdir(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMPLATE_POSTER_DIR", str(tmp_path))
    yield tmp_path


def test_template_poster_upload_and_fetch(template_tmpdir):
    from app.main import app

    client = TestClient(app)
    payload = {
        "slot": "variant_a",
        "filename": "PosterA.png",
        "content_type": "image/png",
        "data": _encode_png((255, 0, 0)),
    }
    response = client.post("/api/template-posters", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["slot"] == "variant_a"
    assert data["poster"]["media_type"] == "image/png"
    assert data["poster"]["width"] == 64
    assert data["poster"]["height"] == 64
    assert data["poster"]["data_url"].startswith("data:image/png;base64,")
    assert data["poster"].get("url") is None

    response = client.get("/api/template-posters")
    assert response.status_code == 200
    listing = response.json()
    assert listing["posters"], "Expected uploaded poster to be listed"
    assert listing["posters"][0]["slot"] == "variant_a"


def test_template_poster_uploads_to_cloudflare(monkeypatch, template_tmpdir):
    import app.services.template_variants as template_variants

    uploaded = {}

    def fake_upload(raw: bytes, *, filename: str, content_type: str):
        uploaded["raw_len"] = len(raw)
        uploaded["filename"] = filename
        uploaded["content_type"] = content_type
        return "template-posters/test/key.png", "https://cdn.example.com/template-posters/test/key.png"

    monkeypatch.setattr(template_variants, "_upload_to_cloudflare", fake_upload)

    record = template_variants.save_template_poster(
        slot="variant_a",
        filename="Cloud.png",
        content_type="image/png",
        data=_encode_png((128, 64, 32)),
    )

    assert record.key == "template-posters/test/key.png"
    assert record.url == "https://cdn.example.com/template-posters/test/key.png"
    assert uploaded["filename"] == "Cloud.png"
    assert uploaded["content_type"] == "image/png"
    assert uploaded["raw_len"] > 0

    posters = template_variants.list_template_posters()
    assert posters[0].url == "https://cdn.example.com/template-posters/test/key.png"


def test_generate_poster_uses_template_overrides(template_tmpdir):
    import app.services.template_variants as template_variants

    template_variants.save_template_poster(
        slot="variant_a",
        filename="alpha.png",
        content_type="image/png",
        data=_encode_png((0, 255, 0)),
    )
    template_variants.save_template_poster(
        slot="variant_b",
        filename="bravo.png",
        content_type="image/png",
        data=_encode_png((0, 0, 255)),
    )

    from app.schemas import PosterInput
    from app.services.glibatree import generate_poster_asset

    poster = PosterInput(
        brand_name="Brand",
        agent_name="Agent",
        scenario_image="scene",
        product_name="Product",
        features=["f1", "f2", "f3"],
        title="Title",
        series_description="Desc",
        subtitle="Sub",
    )

    result = generate_poster_asset(
        poster,
        prompt="prompt",
        preview="preview",
        render_mode="locked",
        variants=2,
    )

    assert result.poster.filename == "alpha.png"
    assert result.variants
    assert result.variants[0].filename == "bravo.png"
