from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _png_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    image = Image.new("RGB", (64, 64), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_bytes(color: tuple[int, int, int] = (200, 100, 50)) -> bytes:
    image = Image.new("RGB", (64, 64), color)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture()
def template_tmpdir(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMPLATE_POSTER_DIR", str(tmp_path))
    yield tmp_path


def test_template_poster_upload_and_fetch(template_tmpdir, monkeypatch):
    from app.main import app
    import app.services.template_variants as template_variants

    raw_png = base64.b64decode(_encode_png((255, 0, 0)))

    def fake_get_bytes(key: str):
        assert key == "template-posters/PosterA.png"
        return raw_png

    monkeypatch.setattr(template_variants, "get_bytes", fake_get_bytes)

    client = TestClient(app)
    key = "template-posters/variant_a/poster-a.png"
    fake_r2_storage[key] = _png_bytes((255, 0, 0))
    payload = {
        "slot": "variant_a",
        "filename": "PosterA.png",
        "content_type": "image/png",
        "key": "template-posters/PosterA.png",
        "size": len(raw_png),
    }
    response = client.post("/api/template-posters", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["slot"] == "variant_a"
    assert data["poster"]["media_type"] == "image/png"
    assert data["poster"]["width"] == 64
    assert data["poster"]["height"] == 64
    assert data["poster"]["url"].startswith("https://cdn.example.com/")
    assert data["poster"]["key"] == key

    response = client.get("/api/template-posters")
    assert response.status_code == 200
    listing = response.json()
    assert listing["posters"], "Expected uploaded poster to be listed"
    assert listing["posters"][0]["slot"] == "variant_a"


def test_template_poster_metadata_uses_existing_r2_key(template_tmpdir, fake_r2_storage):
    import app.services.template_variants as template_variants

    key = "template-posters/test/key.png"
    fake_r2_storage[key] = _png_bytes((128, 64, 32))

    record = template_variants.save_template_poster(
        slot="variant_a",
        filename="Cloud.png",
        content_type="image/png",
        key=key,
        size=len(fake_r2_storage[key]),
    )

    assert record.key == key
    assert record.url == f"https://cdn.example.com/{key}"

    posters = template_variants.list_template_posters()
    assert posters[0].url == f"https://cdn.example.com/{key}"


def test_generate_poster_uses_template_overrides(template_tmpdir, fake_r2_storage):
    import app.services.template_variants as template_variants

    key_a = "template-posters/variant_a/alpha.png"
    fake_r2_storage[key_a] = _png_bytes((0, 255, 0))
    template_variants.save_template_poster(
        slot="variant_a",
        filename="alpha.png",
        content_type="image/png",
        key=key_a,
        size=len(fake_r2_storage[key_a]),
    )
    key_b = "template-posters/variant_b/bravo.png"
    fake_r2_storage[key_b] = _png_bytes((0, 0, 255))
    template_variants.save_template_poster(
        slot="variant_b",
        filename="bravo.png",
        content_type="image/png",
        key=key_b,
        size=len(fake_r2_storage[key_b]),
    )

    from app.schemas import PosterInput
    from app.services.glibatree import generate_poster_asset

    poster = PosterInput(
        brand_name="Brand",
        agent_name="Agent",
        scenario_image="https://cdn.example.com/scene.png",
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


def test_template_poster_accepts_jpeg_variants(template_tmpdir, fake_r2_storage):
    from app.main import app

    client = TestClient(app)
    key_jpeg = "template-posters/variant_a/poster-a.jpeg"
    fake_r2_storage[key_jpeg] = _jpeg_bytes()
    payload_jpeg = {
        "slot": "variant_a",
        "filename": "PosterA.jpeg",
        "content_type": "image/jpeg",
        "key": key_jpeg,
        "size": len(fake_r2_storage[key_jpeg]),
    }
    response = client.post("/api/template-posters", json=payload_jpeg)
    assert response.status_code == 200

    key_jpg = "template-posters/variant_b/poster-b.jpg"
    fake_r2_storage[key_jpg] = _jpeg_bytes((20, 40, 60))
    payload_jpg = {
        "slot": "variant_b",
        "filename": "PosterB.jpg",
        "content_type": "image/jpg",
        "key": key_jpg,
        "size": len(fake_r2_storage[key_jpg]),
    }
    response = client.post("/api/template-posters", json=payload_jpg)
    assert response.status_code == 200


def test_template_poster_invalid_image_returns_detail(template_tmpdir, fake_r2_storage):
    from app.main import app

    client = TestClient(app)
    key = "template-posters/variant_b/broken.png"
    fake_r2_storage[key] = b"not-an-image"
    payload = {
        "slot": "variant_b",
        "filename": "broken.png",
        "content_type": "image/png",
        "key": key,
        "size": len(fake_r2_storage[key]),
    }
    response = client.post("/api/template-posters", json=payload)
    assert response.status_code == 400
    detail = response.json().get("detail")
    assert detail["error"] == "INVALID_IMAGE"
    assert detail["reason"] in {"cannot_identify", "decode_failed"}
