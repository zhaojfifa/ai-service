import inspect
import logging
import os
import time
import uuid
from typing import Any, Optional, Tuple

import vertexai
from google.api_core.exceptions import GoogleAPICallError, NotFound, PermissionDenied
from vertexai.preview.vision_models import ImageGenerationModel

log = logging.getLogger("ai-service")

DEFAULT_MODEL = os.getenv("VERTEX_IMAGEN_MODEL", "imagen-3.0-generate-001")
_ALLOWED_ASPECTS = {"1:1", "16:9", "9:16", "4:3", "3:4"}


def _ensure_credentials_from_b64() -> None:
    """Write credentials from ``GCP_KEY_B64`` to disk if present."""

    key_b64 = os.getenv("GCP_KEY_B64")
    if not key_b64:
        return

    out_path = "/opt/render/project/src/gcp-key.json"
    try:
        import base64
        import pathlib

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
    log.info(
        "vertex.init",
        extra={"project": project, "location": location},
    )


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
    canonical_ratio = ratio if ratio in _ALLOWED_ASPECTS else _aspect_from_dims(width, height)
    size_token = f"{width}x{height}"

    if "size" in params:
        return {"size": size_token}, "size"
    if "image_dimensions" in params:
        return {"image_dimensions": {"width": width, "height": height}}, "image_dimensions"
    if "aspect_ratio" in params:
        return {"aspect_ratio": canonical_ratio}, "aspect_ratio"
    return {}, "default"


class VertexImagenClient:
    """Thin wrapper over ``ImageGenerationModel`` with trace-aware logging."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        start = time.time()
        self._model = ImageGenerationModel.from_pretrained(self.model_name)
        self._generate_params = set(
            inspect.signature(self._model.generate_images).parameters.keys()
        )
        log.info(
            "vertex.model.loaded",
            extra={
                "model": self.model_name,
                "mode": "generate",
                "elapsed_ms": round((time.time() - start) * 1000, 2),
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

        log.info(
            "vertex.call",
            extra={
                "trace": trace_id,
                "mode": "generate",
                "model": self.model_name,
                "size": size_token,
                "size_mode": size_mode,
                "negative_prompt": bool(negative_prompt),
                "guidance": guidance,
                "seed": seed if "seed" in self._generate_params else None,
                "prompt_length": len(prompt),
            },
        )

        start = time.time()
        try:
            response = self._model.generate_images(**kwargs)
            elapsed_ms = (time.time() - start) * 1000
            image_bytes = response.images[0]._image_bytes
            log.info(
                "vertex.done",
                extra={
                    "trace": trace_id,
                    "mode": "generate",
                    "model": self.model_name,
                    "bytes": len(image_bytes),
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )
            if return_trace:
                return image_bytes, trace_id
            return image_bytes
        except NotFound as exc:
            log.error(
                "vertex.error",
                extra={
                    "trace": trace_id,
                    "mode": "generate",
                    "model": self.model_name,
                    "error": "not_found",
                    "message": str(exc),
                },
            )
            raise
        except PermissionDenied as exc:
            log.error(
                "vertex.error",
                extra={
                    "trace": trace_id,
                    "mode": "generate",
                    "model": self.model_name,
                    "error": "permission_denied",
                    "message": str(exc),
                },
            )
            raise
        except GoogleAPICallError as exc:
            log.error(
                "vertex.error",
                extra={
                    "trace": trace_id,
                    "mode": "generate",
                    "model": self.model_name,
                    "error": "api_call_error",
                    "message": str(exc),
                },
            )
            raise
        except Exception as exc:  # pragma: no cover - diagnostics only
            log.exception(
                "vertex.error",
                extra={
                    "trace": trace_id,
                    "mode": "generate",
                    "model": self.model_name,
                    "error": "unknown",
                },
            )
            raise


# Backwards compatibility alias for existing imports
VertexImagen = VertexImagenClient
