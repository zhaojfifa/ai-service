from __future__ import annotations

import base64
import inspect
import logging
import os
import pathlib
from typing import Any, Optional, Tuple

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

log = logging.getLogger("ai-service")
_DEFAULT_ASPECTS = {"1:1", "16:9", "9:16", "4:3", "3:4"}


def _ensure_credentials_from_b64() -> None:
    """Write credentials from ``GCP_KEY_B64`` to disk if present."""

    key_b64 = os.getenv("GCP_KEY_B64")
    if not key_b64:
        return

    out_path = "/opt/render/project/src/gcp-key.json"
    try:
        pathlib.Path(out_path).write_bytes(base64.b64decode(key_b64))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = out_path
        log.info("[creds] wrote service account key to %s from GCP_KEY_B64", out_path)
    except Exception as exc:  # pragma: no cover - diagnostics only
        log.exception("[creds] failed to write key from GCP_KEY_B64: %s", exc)


def init_vertex() -> None:
    """Initialise Vertex AI with environment configuration."""

    _ensure_credentials_from_b64()

    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    if not project:
        raise RuntimeError("Missing env GCP_PROJECT_ID")

    vertexai.init(project=project, location=location)
    log.info("[vertex.init] project=%s location=%s", project, location)


def _normalise_dimensions(
    size: Optional[str],
    width: Optional[int],
    height: Optional[int],
    default: str = "1024x1024",
) -> Tuple[int, int, str]:
    """Normalise size arguments into integer width/height with sane defaults."""

    if width and height:
        w, h = int(width), int(height)
    else:
        token = (size or default or "1024x1024").lower().replace("×", "x").strip()
        try:
            w_str, h_str = token.split("x", 1)
            w, h = int(w_str), int(h_str)
        except Exception:
            try:
                w_str, h_str = default.lower().replace("×", "x").split("x", 1)
                w, h = int(w_str), int(h_str)
            except Exception:
                w, h = 1024, 1024
    w = max(64, w)
    h = max(64, h)
    return w, h, f"{w}x{h}"


def _aspect_from_dims(width: int, height: int) -> str:
    if width == height:
        return "1:1"
    if width * 9 == height * 16:
        return "16:9"
    if width * 16 == height * 9:
        return "9:16"
    if width * 3 == height * 4:
        return "4:3"
    if width * 4 == height * 3:
        return "3:4"
    return "1:1"


def _select_dimension_kwargs(
    params: set[str],
    width: int,
    height: int,
    aspect_ratio: Optional[str],
) -> tuple[dict[str, Any], str]:
    """Choose the appropriate size argument compatible with the SDK version."""

    ratio = (aspect_ratio or "").replace("×", "x").strip().lower()
    canonical_ratio = ratio if ratio in _DEFAULT_ASPECTS else _aspect_from_dims(width, height)
    size_token = f"{width}x{height}"

    if "size" in params:
        return {"size": size_token}, "size"
    if "image_dimensions" in params:
        return {"image_dimensions": {"width": width, "height": height}}, "image_dimensions"
    if "aspect_ratio" in params:
        return {"aspect_ratio": canonical_ratio}, "aspect_ratio"
    return {}, "default"


class VertexImagen3:
    """Lazy, generate-only Imagen client (no edit model)."""

    def __init__(self, project: str | None = None, location: str | None = None):
        _ensure_credentials_from_b64()

        project = project or os.getenv("GCP_PROJECT_ID")
        location = location or os.getenv("GCP_LOCATION", "us-central1")
        if not project:
            raise RuntimeError("GCP_PROJECT_ID is required for Vertex Imagen")

        vertexai.init(project=project, location=location)
        self.project = project
        self.location = location
        self._gen = None
        self.model_generate = os.getenv("VERTEX_IMAGEN_MODEL_GENERATE", "imagen-3.0-generate-001")

    def _ensure_gen(self):
        if self._gen is None:
            self._gen = ImageGenerationModel.from_pretrained(self.model_generate)

    def edit_bytes(self, *_, **__):
        raise NotImplementedError("Imagen edit is not available in this service")

    def generate_bytes(
        self,
        prompt: str,
        size: str | None = None,
        guidance: float | None = None,
    ) -> bytes:
        self._ensure_gen()

        # size parsing
        w, h = 1024, 1024
        if size:
            try:
                w, h = [int(x) for x in size.lower().split("x")]
            except Exception:
                pass

        kwargs = dict(prompt=prompt, number_of_images=1, safety_filter_level="block_few")

        # Prefer 'size', fallback to 'image_dimensions'
        sig = ImageGenerationModel.generate_images.__signature__.parameters
        if "size" in sig:
            kwargs["size"] = f"{w}x{h}"
        elif "image_dimensions" in sig:
            kwargs["image_dimensions"] = (w, h)

        if guidance is not None:
            if "guidance" in sig:
                kwargs["guidance"] = guidance
            elif "guidance_scale" in sig:
                kwargs["guidance_scale"] = guidance

        res = self._gen.generate_images(**kwargs)
        return res.images[0]._image_bytes


VertexImagen = VertexImagen3
