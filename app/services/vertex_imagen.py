import inspect
import logging
import os
import time
import uuid
from typing import Optional, Tuple

import vertexai
from google.api_core.exceptions import GoogleAPICallError, NotFound, PermissionDenied
from vertexai.preview.vision_models import ImageGenerationModel

log = logging.getLogger("ai-service")


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
    log.info("[vertex.init] project=%s location=%s", project, location)


def _parse_size(size: str) -> Tuple[int, int]:
    try:
        w, h = [int(x) for x in size.lower().split("x")]
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except Exception:
        return 1024, 1024


class VertexImagen:
    """Thin wrapper over ``ImageGenerationModel`` with trace-aware logging."""

    def __init__(self, model_name: str = "imagen-3.0-generate-001") -> None:
        self.model_name = model_name
        start = time.time()
        self._model = ImageGenerationModel.from_pretrained(self.model_name)
        self._sig_params = set(
            inspect.signature(self._model.generate_images).parameters.keys()
        )
        log.info(
            "[vertex.model] loaded name=%s in %.0fms; params=%s",
            self.model_name,
            (time.time() - start) * 1000,
            sorted(self._sig_params),
        )

    def generate_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        negative_prompt: Optional[str] = None,
        safety_filter_level: str = "block_few",
        seed: Optional[int] = None,
        return_trace: bool = False,
    ) -> bytes | tuple[bytes, str]:
        """Generate a single image and return the binary payload.

        When ``return_trace`` is true the trace id is returned alongside the
        bytes to allow upstream callers to expose it in responses.
        """

        trace_id = uuid.uuid4().hex[:8]
        w, h = _parse_size(size)

        kwargs = {
            "prompt": prompt,
            "number_of_images": 1,
            "safety_filter_level": safety_filter_level,
        }
        if negative_prompt and "negative_prompt" in self._sig_params:
            kwargs["negative_prompt"] = negative_prompt
        if seed is not None and "seed" in self._sig_params:
            kwargs["seed"] = seed

        if "size" in self._sig_params:
            kwargs["size"] = f"{w}x{h}"
        elif "image_dimensions" in self._sig_params:
            kwargs["image_dimensions"] = (w, h)
        elif "aspect_ratio" in self._sig_params:
            ratio = f"{w}:{h}"
            allowed = {"1:1", "16:9", "9:16", "4:3", "3:4"}
            kwargs["aspect_ratio"] = ratio if ratio in allowed else "1:1"

        log.info(
            "[vertex.call>%s] model=%s size=%s neg=%s len(prompt)=%d kwargs=%s",
            trace_id,
            self.model_name,
            size,
            bool(negative_prompt),
            len(prompt),
            {k: v for k, v in kwargs.items() if k != "prompt"},
        )

        start = time.time()
        try:
            response = self._model.generate_images(**kwargs)
            elapsed_ms = (time.time() - start) * 1000
            img_bytes = response.images[0]._image_bytes
            log.info(
                "[vertex.done>%s] ok bytes=%d time=%.0fms",
                trace_id,
                len(img_bytes),
                elapsed_ms,
            )
            if return_trace:
                return img_bytes, trace_id
            return img_bytes
        except NotFound as exc:
            log.error(
                "[vertex.err>%s] NOT_FOUND model=%s: %s", trace_id, self.model_name, exc
            )
            raise
        except PermissionDenied as exc:
            log.error("[vertex.err>%s] PERMISSION_DENIED: %s", trace_id, exc)
            raise
        except GoogleAPICallError as exc:
            log.error("[vertex.err>%s] API_CALL_ERROR: %s", trace_id, exc)
            raise
        except Exception as exc:  # pragma: no cover - diagnostics only
            log.exception("[vertex.err>%s] UNKNOWN: %s", trace_id, exc)
            raise
