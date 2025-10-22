from __future__ import annotations

import base64
import io
import json
import os
import tempfile
from typing import Any, Dict, Optional, Tuple

from PIL import Image as PILImage, ImageDraw
from google.cloud import aiplatform
from vertexai import init as vertex_init
from vertexai.preview.vision_models import (
    ImageGenerationModel,
    Image as VImage,
)

from app.services.vertex_imagen import _ensure_credentials_from_b64


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


def _parse_size(size: Optional[str], width: Optional[int], height: Optional[int], default: str) -> Tuple[int, int]:
    if width and height:
        return int(width), int(height)
    s = (size or default or "1024x1024").lower().replace("×", "x").strip()
    try:
        w, h = [int(x) for x in s.split("x")]
        return max(64, w), max(64, h)
    except Exception:
        return 1024, 1024


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
        self.model_edit = os.getenv("VERTEX_IMAGEN_MODEL_EDIT", "imagen-3.0-edit")
        self.timeout = int(os.getenv("VERTEX_TIMEOUT_SECONDS", "60") or "60")
        self.safety = os.getenv("VERTEX_SAFETY_FILTER_LEVEL", "block_some")  # block_few|block_some|block_most
        seed_env = os.getenv("VERTEX_SEED", "0")
        self.seed = int(seed_env) if str(seed_env).isdigit() and int(seed_env) != 0 else None

        if not self.project:
            raise RuntimeError("GCP_PROJECT_ID is required for Vertex Imagen3")

        aiplatform.init(project=self.project, location=self.location)
        vertex_init(project=self.project, location=self.location)

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
    ) -> bytes:
        w, h = _parse_size(size, width, height, default="1024x1024")

        model = ImageGenerationModel.from_pretrained(self.model_generate)
        kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "number_of_images": max(1, number_of_images),
            "image_dimensions": {"width": w, "height": h},
            "safety_filter_level": self.safety,
            "negative_prompt": negative_prompt,
            "seed": self.seed,
        }
        if guidance is not None:
            kwargs["guidance"] = guidance

        images = model.generate_images(**kwargs, request_timeout=self.timeout)
        if not images:
            raise RuntimeError("Vertex Imagen3 generate_images returned empty list")

        img0 = images[0]
        if hasattr(img0, "image_bytes") and img0.image_bytes:
            return img0.image_bytes
        return _pil_to_bytes(img0._pil_image)  # type: ignore[attr-defined]

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
    ) -> bytes:
        if not base_image_bytes and base_image_b64:
            base_image_bytes = base64.b64decode(base_image_b64)
        if not base_image_bytes:
            raise RuntimeError("edit_bytes requires base_image (bytes or b64)")

        base_vimg = VImage.load_from_bytes(base_image_bytes)
        w, h = _parse_size(size, width, height, default="1024x1024")

        vmask: Optional[VImage] = None
        if mask_b64:
            vmask = VImage.load_from_bytes(base64.b64decode(mask_b64))
        elif region_rect:
            rx = int(region_rect.get("x", 0))
            ry = int(region_rect.get("y", 0))
            rw = int(region_rect.get("width", w))
            rh = int(region_rect.get("height", h))
            m_bytes = _rect_mask_bytes(w, h, rx, ry, rw, rh)
            vmask = VImage.load_from_bytes(m_bytes)

        model = ImageGenerationModel.from_pretrained(self.model_edit)
        kwargs: Dict[str, Any] = {
            "base_image": base_vimg,
            "prompt": prompt,
            "number_of_images": 1,
            "image_dimensions": {"width": w, "height": h},
            "safety_filter_level": self.safety,
            "negative_prompt": negative_prompt,
            "seed": self.seed,
        }
        if vmask:
            kwargs["mask"] = vmask
        if guidance is not None:
            kwargs["guidance"] = guidance

        images = model.edit_image(**kwargs, request_timeout=self.timeout)
        if not images:
            raise RuntimeError("Vertex Imagen3 edit_image returned empty list")

        img0 = images[0]
        if hasattr(img0, "image_bytes") and img0.image_bytes:
            return img0.image_bytes
        return _pil_to_bytes(img0._pil_image)  # type: ignore[attr-defined]
