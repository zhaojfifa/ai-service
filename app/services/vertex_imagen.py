import base64
import inspect
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple

import vertexai
from google.api_core.exceptions import GoogleAPICallError, NotFound, PermissionDenied
from vertexai.preview.vision_models import ImageGenerationModel

logger = logging.getLogger("ai-service")

DEFAULT_MODEL = "imagen-3.0-generate-001"
_ALLOWED_ASPECTS = {"1:1", "16:9", "9:16", "4:3", "3:4"}


def _ensure_credentials_from_b64() -> None:
    """Write credentials from ``GCP_KEY_B64`` to disk if present."""

    key_b64 = os.getenv("GCP_KEY_B64")
    if not key_b64:
        return

    out_path = Path("/opt/render/project/src/gcp-key.json")
    try:
        out_path.write_bytes(base64.b64decode(key_b64))
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.exception("[creds] failed to write key from GCP_KEY_B64: %s", exc)
        return

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(out_path)
    logger.info("[creds] wrote service account key to %s from GCP_KEY_B64", out_path)


def _ensure_credentials_from_json_env() -> None:
    """Persist ``GOOGLE_APPLICATION_CREDENTIALS_JSON`` into a temp file if present."""

    gac_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
    if not gac_json:
        return

    try:
        try:
            data = json.loads(gac_json)
        except json.JSONDecodeError:
            data = json.loads(gac_json.encode("utf-8").decode("unicode_escape"))
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.exception("[creds] invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: %s", exc)
        return

    fd, path = tempfile.mkstemp(prefix="gac-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
    logger.info("[creds] wrote temporary GOOGLE_APPLICATION_CREDENTIALS to %s", path)


def _normalise_dimensions(
    size: Optional[str],
    width: Optional[int],
    height: Optional[int],
    default: str = "1024x1024",
) -> Tuple[int, int, str]:
    """Normalise size arguments into integer width/height with safe defaults."""

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
    canonical_ratio = ratio if ratio in _ALLOWED_ASPECTS else _aspect_from_dims(width, height)
    size_token = f"{width}x{height}"

    if "size" in params:
        return {"size": size_token}, "size"
    if "image_dimensions" in params:
        return {"image_dimensions": (width, height)}, "image_dimensions"
    if "aspect_ratio" in params:
        return {"aspect_ratio": canonical_ratio}, "aspect_ratio"
    return {}, "default"


class VertexImagen3:
    """Google Vertex AI Imagen3 generation adapter with SDK compatibility helpers."""

    def __init__(self, project: str, location: str = "us-central1", model_name: str = DEFAULT_MODEL):
        if not project:
            raise RuntimeError("GCP_PROJECT_ID is required for Vertex Imagen3")

        self.project = project
        self.location = location or "us-central1"
        self.model_name = model_name or DEFAULT_MODEL

        _ensure_credentials_from_b64()
        _ensure_credentials_from_json_env()

        vertexai.init(project=self.project, location=self.location)

        start = time.time()
        self._model = ImageGenerationModel.from_pretrained(self.model_name)
        self._generate_params = set(
            inspect.signature(self._model.generate_images).parameters.keys()
        )
        logger.info(
            "[vertex.model] loaded name=%s in %.0fms", 
            self.model_name,
            (time.time() - start) * 1000,
            extra={
                "project": self.project,
                "location": self.location,
                "model": self.model_name,
                "params": sorted(self._generate_params),
            },
        )

    def generate_bytes(
        self,
        *,
        prompt: str,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        safety_filter_level: str = "block_few",
        seed: Optional[int] = None,
        guidance: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
        return_trace: bool = False,
    ) -> bytes | tuple[bytes, str]:
        """Generate a single image and return the binary payload."""

        trace_id = uuid.uuid4().hex[:8]
        width_px, height_px, size_token = _normalise_dimensions(size, width, height)
        ratio_value = aspect_ratio or _aspect_from_dims(width_px, height_px)
        size_kwargs, size_mode = _select_dimension_kwargs(
            self._generate_params, width_px, height_px, ratio_value
        )

        kwargs: dict[str, Any] = {
            "prompt": prompt,
            "number_of_images": 1,
        }
        if "safety_filter_level" in self._generate_params:
            kwargs["safety_filter_level"] = safety_filter_level
        if negative_prompt and "negative_prompt" in self._generate_params:
            kwargs["negative_prompt"] = negative_prompt
        if seed is not None and "seed" in self._generate_params:
            kwargs["seed"] = seed
        if guidance is not None and "guidance" in self._generate_params:
            kwargs["guidance"] = guidance
        kwargs.update(size_kwargs)

        logger.info(
            "[vertex.call] trace=%s model=%s size=%s mode=%s neg=%s seed=%s guidance=%s len_prompt=%d",
            trace_id,
            self.model_name,
            size_token,
            size_mode,
            bool(negative_prompt),
            seed if seed is not None else None,
            guidance,
            len(prompt),
        )

        start = time.time()
        try:
            response = self._model.generate_images(**kwargs)
            elapsed_ms = (time.time() - start) * 1000
            image_bytes = response.images[0]._image_bytes
            logger.info(
                "[vertex.done] trace=%s bytes=%d time=%.0fms",
                trace_id,
                len(image_bytes),
                elapsed_ms,
            )
            if return_trace:
                return image_bytes, trace_id
            return image_bytes
        except NotFound as exc:
            logger.error("[vertex.err] trace=%s NOT_FOUND model=%s", trace_id, self.model_name)
            raise
        except PermissionDenied as exc:
            logger.error("[vertex.err] trace=%s PERMISSION_DENIED: %s", trace_id, exc)
            raise
        except GoogleAPICallError as exc:
            logger.error("[vertex.err] trace=%s API_CALL_ERROR: %s", trace_id, exc)
            raise
        except Exception as exc:  # pragma: no cover - diagnostics only
            logger.exception("[vertex.err] trace=%s UNKNOWN: %s", trace_id, exc)
            raise


# Backwards compatibility alias for legacy imports
VertexImagen = VertexImagen3
