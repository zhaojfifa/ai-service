from __future__ import annotations

import base64
import io
import json
import inspect
import logging
import os
import tempfile
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from PIL import Image as PILImage, ImageDraw
from google.cloud import aiplatform
from vertexai import init as vertex_init
from vertexai.preview.vision_models import (
    ImageGenerationModel,
    Image as VImage,
)

from app.services.vertex_imagen import (
    _aspect_from_dims,
    _ensure_credentials_from_b64,
    _normalise_dimensions,
    _select_dimension_kwargs,
)


logger = logging.getLogger("ai-service")


def _ensure_gcp_auth_via_json_env() -> None:
    """若提供 GOOGLE_APPLICATION_CREDENTIALS_JSON，则写临时文件并设置 GAC 路径。"""

    gac_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
    if gac_json:
        try:
            data = json.loads(gac_json)
        except Exception:
            data = json.loads(gac_json.encode("utf-8").decode("unicode_escape"))
        fd, path = tempfile.mkstemp(prefix="gac-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path


def _pil_to_bytes(img: PILImage.Image, fmt: str = "JPEG") -> bytes:
    bio = io.BytesIO()
    img.save(bio, fmt, quality=92)
    return bio.getvalue()


def _rect_mask_bytes(w: int, h: int, x: int, y: int, rw: int, rh: int) -> bytes:
    """白=编辑；黑=保留。"""

    mask = PILImage.new("L", (w, h), color=0)  # 黑=不编辑
    draw = ImageDraw.Draw(mask)
    draw.rectangle([x, y, x + rw, y + rh], fill=255)  # 白=编辑
    bio = io.BytesIO()
    mask.save(bio, "PNG")
    return bio.getvalue()


class VertexImagen3:
    """Google Vertex AI Imagen3 适配层：生图 + 局部编辑。"""

    def __init__(self) -> None:
        _ensure_credentials_from_b64()
        _ensure_gcp_auth_via_json_env()

        self.project = os.getenv("GCP_PROJECT_ID") or ""
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        self.model_generate = os.getenv("VERTEX_IMAGEN_MODEL_GENERATE", "imagen-3.0-generate-001")
        self.model_edit_name = os.getenv("VERTEX_IMAGEN_MODEL_EDIT", "imagen-3.0-edit")
        self.enable_edit = os.getenv("VERTEX_IMAGEN_ENABLE_EDIT", "").lower() in {"1", "true", "yes"}
        self.model_edit = self.model_edit_name if self.enable_edit else None
        self.timeout = int(os.getenv("VERTEX_TIMEOUT_SECONDS", "60") or "60")
        self.safety = os.getenv("VERTEX_SAFETY_FILTER_LEVEL", "block_some")  # block_few|block_some|block_most
        seed_env = os.getenv("VERTEX_SEED", "0")
        self.seed = int(seed_env) if str(seed_env).isdigit() and int(seed_env) != 0 else None

        if not self.project:
            raise RuntimeError("GCP_PROJECT_ID is required for Vertex Imagen3")

        aiplatform.init(project=self.project, location=self.location)
        vertex_init(project=self.project, location=self.location)

        self._generate_model = ImageGenerationModel.from_pretrained(self.model_generate)
        self._generate_params = set(
            inspect.signature(self._generate_model.generate_images).parameters.keys()
        )
        if self.enable_edit:
            self._edit_model = ImageGenerationModel.from_pretrained(self.model_edit_name)
            self._edit_params = set(
                inspect.signature(self._edit_model.edit_image).parameters.keys()
            )
        else:
            self._edit_model = None
            self._edit_params = set()

        logger.info(
            "[vertex3.model] params generate=%s edit=%s enabled=%s",
            sorted(self._generate_params),
            sorted(self._edit_params) if self._edit_params else [],
            self.enable_edit,
        )

    # ---------- 生图 ----------
    def generate_bytes(
        self,
        *,
        prompt: str,
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        aspect_ratio: Optional[str] = None,  # 兼容上层，无需强制
        number_of_images: int = 1,
        guidance: Optional[float] = None,
        return_trace: bool = False,
    ) -> bytes | tuple[bytes, str]:
        width_px, height_px, size_token = _normalise_dimensions(
            size, width, height, default="1024x1024"
        )

        trace_id = uuid.uuid4().hex[:8]
        ratio_value = aspect_ratio or _aspect_from_dims(width_px, height_px)
        size_kwargs, size_mode = _select_dimension_kwargs(
            self._generate_params, width_px, height_px, ratio_value
        )

        kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "number_of_images": max(1, number_of_images),
        }
        if "safety_filter_level" in self._generate_params:
            kwargs["safety_filter_level"] = self.safety
        if negative_prompt and "negative_prompt" in self._generate_params:
            kwargs["negative_prompt"] = negative_prompt
        if self.seed is not None and "seed" in self._generate_params:
            kwargs["seed"] = self.seed
        if guidance is not None and "guidance" in self._generate_params:
            kwargs["guidance"] = guidance
        kwargs.update(size_kwargs)

        logger.info(
            "[vertex3.call>%s] mode=generate size=%s mode=%s neg=%s guidance=%s",
            trace_id,
            size_token,
            size_mode,
            bool(negative_prompt),
            guidance,
        )
        start = time.time()
        if "request_timeout" in self._generate_params:
            kwargs["request_timeout"] = self.timeout

        images = self._generate_model.generate_images(**kwargs)
        if not images:
            raise RuntimeError("Vertex Imagen3 generate_images returned empty list")

        img0 = images[0]
        if hasattr(img0, "image_bytes") and img0.image_bytes:
            data = img0.image_bytes
        else:
            data = _pil_to_bytes(img0._pil_image)  # type: ignore[attr-defined]

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "[vertex3.done>%s] mode=generate bytes=%d time=%.0fms",
            trace_id,
            len(data),
            elapsed_ms,
        )
        if return_trace:
            return data, trace_id
        return data

    # ---------- 局部编辑 / Inpainting ----------
    def edit_bytes(
        self,
        *,
        base_image_b64: Optional[str] = None,
        base_image_bytes: Optional[bytes] = None,
        prompt: str,
        mask_b64: Optional[str] = None,
        region_rect: Optional[Dict[str, int]] = None,  # {x,y,width,height}
        size: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        guidance: Optional[float] = None,
        return_trace: bool = False,
    ) -> bytes | tuple[bytes, str]:
        if not self.enable_edit or self._edit_model is None:
            raise RuntimeError(
                "Vertex Imagen3 edit support is disabled. Set VERTEX_IMAGEN_ENABLE_EDIT=1 to enable."
            )

        if not base_image_bytes and base_image_b64:
            base_image_bytes = base64.b64decode(base_image_b64)
        if not base_image_bytes:
            raise RuntimeError("edit_bytes requires base_image (bytes or b64)")

        base_vimg = VImage.load_from_bytes(base_image_bytes)
        width_px, height_px, size_token = _normalise_dimensions(
            size, width, height, default="1024x1024"
        )

        trace_id = uuid.uuid4().hex[:8]
        vmask: Optional[VImage] = None
        if mask_b64:
            vmask = VImage.load_from_bytes(base64.b64decode(mask_b64))
        elif region_rect:
            rx = int(region_rect.get("x", 0))
            ry = int(region_rect.get("y", 0))
            rw = int(region_rect.get("width", width_px))
            rh = int(region_rect.get("height", height_px))
            m_bytes = _rect_mask_bytes(width_px, height_px, rx, ry, rw, rh)
            vmask = VImage.load_from_bytes(m_bytes)

        size_kwargs, size_mode = _select_dimension_kwargs(
            self._edit_params, width_px, height_px, _aspect_from_dims(width_px, height_px)
        )
        kwargs: Dict[str, Any] = {
            "base_image": base_vimg,
            "prompt": prompt,
            "number_of_images": 1,
        }
        if "safety_filter_level" in self._edit_params:
            kwargs["safety_filter_level"] = self.safety
        if negative_prompt and "negative_prompt" in self._edit_params:
            kwargs["negative_prompt"] = negative_prompt
        if self.seed is not None and "seed" in self._edit_params:
            kwargs["seed"] = self.seed
        if vmask and "mask" in self._edit_params:
            kwargs["mask"] = vmask
        if guidance is not None and "guidance" in self._edit_params:
            kwargs["guidance"] = guidance
        kwargs.update(size_kwargs)

        logger.info(
            "[vertex3.call>%s] mode=edit size=%s mode=%s mask=%s guidance=%s",
            trace_id,
            size_token,
            size_mode,
            bool(vmask),
            guidance,
        )
        start = time.time()
        if "request_timeout" in self._edit_params:
            kwargs["request_timeout"] = self.timeout

        images = self._edit_model.edit_image(**kwargs)
        if not images:
            raise RuntimeError("Vertex Imagen3 edit_image returned empty list")

        img0 = images[0]
        if hasattr(img0, "image_bytes") and img0.image_bytes:
            data = img0.image_bytes
        else:
            data = _pil_to_bytes(img0._pil_image)  # type: ignore[attr-defined]

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "[vertex3.done>%s] mode=edit bytes=%d time=%.0fms",
            trace_id,
            len(data),
            elapsed_ms,
        )
        if return_trace:
            return data, trace_id
        return data
