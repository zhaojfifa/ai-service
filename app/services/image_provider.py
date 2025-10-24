import base64
import io
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException


def _parse_size(size: Optional[str], width: Optional[int], height: Optional[int], default: str) -> Tuple[int, int]:
    if width and height:
        return int(width), int(height)
    s = (size or default or "").lower().replace("×", "x").strip()
    try:
        w, h = [int(x) for x in s.split("x")]
        return max(1, w), max(1, h)
    except Exception:
        return 1024, 1024


class ImageProvider:
    """
    统一图片生成适配层（优先 Vertex → 回退 OpenAI 兼容 → 占位图）：
      - Vertex 直连: POST <base>/generate (返回 image/jpeg 字节)
      - OpenAI 兼容: POST <base or /v1>/images/generations -> { data: [{ b64_json }] }
    """

    def __init__(self) -> None:
        self.base = os.getenv("IMAGE_API_BASE", "").rstrip("/")
        self.api_key = os.getenv("IMAGE_API_KEY", "")
        self.kind = (os.getenv("IMAGE_API_KIND", "auto") or "auto").lower()
        self.proxy = os.getenv("IMAGE_API_PROXY", "") or None
        self.default_size = os.getenv("IMAGE_DEFAULT_SIZE", "1024x1024")

    def generate(self, *, prompt: str, size: Optional[str] = None,
                 width: Optional[int] = None, height: Optional[int] = None,
                 aspect_ratio: Optional[str] = None) -> bytes:

        w, h = _parse_size(size, width, height, self.default_size)

        if not self.base:
            return self._placeholder(prompt=prompt, width=w, height=h)

        mode = self._decide_kind()

        if mode == "vertex":
            return self._gen_vertex(prompt=prompt, size=f"{w}x{h}", ar=aspect_ratio)
        if mode == "openai":
            return self._gen_openai(prompt=prompt, size=f"{w}x{h}", ar=aspect_ratio)

        v_ok, v_bytes, v_err = self._try_vertex(prompt=prompt, size=f"{w}x{h}", ar=aspect_ratio)
        if v_ok:
            return v_bytes  # type: ignore

        o_ok, o_bytes, o_err = self._try_openai(prompt=prompt, size=f"{w}x{h}", ar=aspect_ratio)
        if o_ok:
            return o_bytes  # type: ignore

        raise HTTPException(
            status_code=502,
            detail=f"image generation failed (vertex error={v_err}; openai-compatible error={o_err})"
        )

    def _try_vertex(self, *, prompt: str, size: str, ar: Optional[str]):
        try:
            return True, self._gen_vertex(prompt=prompt, size=size, ar=ar), None
        except Exception as e:
            return False, None, str(e)

    def _try_openai(self, *, prompt: str, size: str, ar: Optional[str]):
        try:
            return True, self._gen_openai(prompt=prompt, size=size, ar=ar), None
        except Exception as e:
            return False, None, str(e)

    def _gen_openai(self, *, prompt: str, size: str, ar: Optional[str]) -> bytes:
        url = f"{self.base}/v1/images/generations" if not self.base.endswith("/v1") else f"{self.base}/images/generations"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }
        if ar:
            payload["aspect_ratio"] = ar

        try:
            with httpx.Client(proxies=self.proxy, timeout=60) as client:
                r = client.post(url, json=payload, headers=headers)
                if r.status_code >= 400:
                    raise HTTPException(status_code=r.status_code, detail=r.text)
                data = r.json()
                b64 = data["data"][0]["b64_json"]
                return base64.b64decode(b64)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"openai-compatible error: {e}")

    def _gen_vertex(self, *, prompt: str, size: str, ar: Optional[str]) -> bytes:
        url = f"{self.base}/generate"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {"prompt": prompt, "size": size}
        if ar:
            payload["aspect_ratio"] = ar

        try:
            with httpx.Client(proxies=self.proxy, timeout=60) as client:
                r = client.post(url, json=payload, headers=headers)
                if r.status_code >= 400:
                    raise HTTPException(status_code=r.status_code, detail=r.text)
                return r.content
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"vertex-direct error: {e}")

    def _placeholder(self, *, prompt: str, width: int, height: int) -> bytes:
        img = Image.new("RGB", (width, height), "#f2f2f2")
        draw = ImageDraw.Draw(img)
        msg = f"[PLACEHOLDER]\n{prompt}"
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
        tw, th = draw.multiline_textbbox((0, 0), msg, font=font, align="center")[2:]
        draw.multiline_text(((width - tw) / 2, (height - th) / 2), msg, fill="#333", font=font, align="center")

        bio = io.BytesIO()
        img.save(bio, "JPEG", quality=92)
        return bio.getvalue()

    def _decide_kind(self) -> str:
        if self.kind in {"openai", "vertex"}:
            return self.kind
        return "auto"
