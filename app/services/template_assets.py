from __future__ import annotations

import base64
import binascii
import logging
from io import BytesIO
from pathlib import Path

from PIL import Image

log = logging.getLogger(__name__)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPG_MAGIC = b"\xff\xd8\xff"


def _looks_like_base64_text(s: str) -> bool:
    ss = s.strip()
    if not ss:
        return False
    if ss.startswith("data:image/"):
        return True
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r"
    ratio = sum(1 for ch in ss[:2000] if ch in allowed) / max(1, min(len(ss), 2000))
    return ratio > 0.95


def decode_image_bytes_from_b64_text(text: str) -> bytes:
    t = text.strip()
    if t.startswith("data:image/"):
        comma = t.find(",")
        if comma >= 0:
            t = t[comma + 1 :].strip()
    try:
        return base64.b64decode(t, validate=False)
    except binascii.Error as e:
        raise ValueError(f"invalid base64 content: {e}") from e


def detect_magic(b: bytes) -> str:
    if b.startswith(PNG_MAGIC):
        return "png"
    if b.startswith(JPG_MAGIC):
        return "jpg"
    return "unknown"


def read_template_bytes(path: Path) -> bytes:
    if path.suffix.lower() == ".b64":
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not _looks_like_base64_text(text):
            log.warning("template .b64 file does not look like base64: %s", path)
        return decode_image_bytes_from_b64_text(text)
    return path.read_bytes()


def open_image_from_any_template_file(path: Path) -> Image.Image:
    """Supports *.png/*.jpg/*.webp binary and *.b64 text (base64 or data URL)."""
    if not path.exists():
        raise FileNotFoundError(str(path))

    raw = read_template_bytes(path)
    log.info(
        "[template] open path=%s suffix=%s bytes=%d magic=%s head=%s",
        str(path),
        path.suffix.lower(),
        len(raw),
        detect_magic(raw),
        raw[:16].hex(),
    )
    img = Image.open(BytesIO(raw))
    img.load()
    return img
