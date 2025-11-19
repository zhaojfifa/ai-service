"""Helpers for managing uploaded template poster variants used for A/B testing."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional

from PIL import Image, UnidentifiedImageError

from app.schemas import PosterImage
from app.services.s3_client import get_bytes, public_url_for

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}
DEFAULT_SLOTS = ("variant_a", "variant_b")


@dataclass
class TemplatePosterRecord:
    slot: str
    filename: str
    content_type: str
    path: Path | None
    width: int
    height: int
    key: str | None = None
    url: str | None = None


def _storage_dir() -> Path:
    custom = os.getenv("TEMPLATE_POSTER_DIR")
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parents[1] / "data" / "template_posters"


def _metadata_path() -> Path:
    return _storage_dir() / "metadata.json"


def _ensure_storage_dir() -> Path:
    directory = _storage_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _clean_filename(name: str) -> str:
    stem = re.sub(r"[^0-9A-Za-z._-]", "_", name or "poster")
    return stem or "poster.png"


def _extension_for(content_type: str) -> str:
    if content_type == "image/png":
        return ".png"
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/webp":
        return ".webp"
    raise ValueError(f"Unsupported content type: {content_type}")


def _read_metadata() -> dict[str, dict[str, str]]:
    meta_path = _metadata_path()
    if not meta_path.exists():
        return {}
    try:
        with meta_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload  # type: ignore[return-value]
    except json.JSONDecodeError:  # pragma: no cover - corrupted file
        return {}
    return {}


def _write_metadata(data: dict[str, dict[str, str]]) -> None:
    meta_path = _metadata_path()
    _ensure_storage_dir()
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _remove_existing_slot_files(slot: str) -> None:
    directory = _ensure_storage_dir()
    for path in directory.glob(f"{slot}.*"):
        try:
            path.unlink()
        except OSError:  # pragma: no cover - ignore cleanup failures
            continue


def _poster_from_record(record: TemplatePosterRecord) -> PosterImage:
    raw: bytes | None = None
    if record.path and record.path.exists():
        with record.path.open("rb") as handle:
            raw = handle.read()
    elif record.key:
        try:
            raw = get_bytes(record.key)
        except Exception:  # pragma: no cover - network/config failure fallback
            logger.warning("Failed to fetch template poster %s from R2", record.key)

    data_url: str | None = None
    if raw:
        data_url = f"data:{record.content_type};base64,{base64.b64encode(raw).decode()}"
    payload = {
        "filename": record.filename,
        "media_type": record.content_type,
        "data_url": data_url,
        "url": record.url,
        "key": record.key,
        "width": record.width,
        "height": record.height,
    }
    if hasattr(PosterImage, "model_validate"):
        return PosterImage.model_validate(payload)  # type: ignore[arg-type]
    return PosterImage(**payload)


def _load_record(slot: str, meta: dict[str, dict[str, str]]) -> TemplatePosterRecord | None:
    entry = meta.get(slot)
    if not entry:
        return None
    filename = entry.get("filename") or f"{slot}.png"
    content_type = entry.get("content_type") or "image/png"
    try:
        ext = _extension_for(content_type)
    except ValueError:
        ext = ".png"
    directory = _ensure_storage_dir()
    path_value = entry.get("path") or f"{slot}{ext}"
    path = directory / path_value if path_value else None
    if path and not path.exists():
        path = None

    width = int(entry.get("width") or 0)
    height = int(entry.get("height") or 0)

    if (width <= 0 or height <= 0) and path and path.exists():
        with path.open("rb") as handle:
            raw = handle.read()
        with Image.open(BytesIO(raw)) as image:
            width, height = image.size

    if width <= 0 or height <= 0:
        return None

    return TemplatePosterRecord(
        slot=slot,
        filename=filename,
        content_type=content_type,
        path=path,
        width=width,
        height=height,
        key=entry.get("key"),
        url=entry.get("url"),
    )


def list_template_posters() -> list[PosterImage]:
    meta = _read_metadata()
    posters: list[PosterImage] = []
    for slot in DEFAULT_SLOTS:
        record = _load_record(slot, meta)
        if not record:
            continue
        posters.append(_poster_from_record(record))
    return posters


def iter_template_records() -> Iterable[TemplatePosterRecord]:
    meta = _read_metadata()
    for slot in DEFAULT_SLOTS:
        record = _load_record(slot, meta)
        if record:
            yield record


def save_template_poster(
    *,
    slot: str,
    filename: str,
    content_type: str,
    key: str,
    size: int | None = None,
    allowed_mime: Optional[set[str]] = None,
) -> TemplatePosterRecord:
    slot = slot.strip()
    logger.info(
        "[poster-upload] Start processing",
        extra={
            "slot": slot,
            "poster_filename": filename,
            "content_type": content_type,
            "storage_key": key,
            "reported_size": size,
        },
    )

    if slot not in DEFAULT_SLOTS:
        logger.warning("[poster-upload] Invalid slot", extra={"slot": slot})
        raise ValueError("slot must be one of variant_a or variant_b")

    content_type = content_type.strip().lower()
    key = (key or "").strip()
    if not key:
        logger.warning("[poster-upload] Missing storage key", extra={"slot": slot})
        raise ValueError("缺少对象存储 key，请先完成 R2 上传。")

    allowed = allowed_mime or DEFAULT_ALLOWED_MIME
    if content_type not in allowed:
        logger.warning(
            "[poster-upload] Unsupported content type",
            extra={"slot": slot, "content_type": content_type},
        )
        raise ValueError("Unsupported image content type")

    try:
        raw = get_bytes(key)
    except Exception as exc:  # pragma: no cover - networking/config issues
        logger.exception(
            "[poster-upload] Failed to download uploaded template from R2",
            extra={"slot": slot, "key": key},
        )
        raise ValueError("无法从对象存储读取模板文件，请稍后重试。") from exc

    if not raw:
        logger.warning(
            "[poster-upload] Image payload is empty after fetching from R2",
            extra={"slot": slot, "content_type": content_type, "key": key},
        )
        raise ValueError("对象存储返回空文件，请重新上传。")

    try:
        with Image.open(BytesIO(raw)) as image:
            image.load()
            width, height = image.size
    except UnidentifiedImageError as exc:
        logger.error(
            "[poster-upload] Cannot identify image file (possibly corrupted)",
            extra={"slot": slot, "content_type": content_type},
        )
        raise ValueError("Invalid image payload") from exc
    except Exception as exc:
        logger.exception(
            "[poster-upload] Unexpected error while opening image",
            extra={"slot": slot, "content_type": content_type},
        )
        raise ValueError("Invalid image payload") from exc

    safe_filename = _clean_filename(filename)
    ext = _extension_for(content_type)

    directory = _ensure_storage_dir()
    _remove_existing_slot_files(slot)
    path = directory / f"{slot}{ext}"
    try:
        with path.open("wb") as handle:
            handle.write(raw)
        logger.info(
            "[poster-upload] Image written",
            extra={"slot": slot, "path": str(path), "width": width, "height": height},
        )
    except Exception as exc:
        logger.exception(
            "[poster-upload] Failed to write image to disk",
            extra={"slot": slot, "path": str(path)},
        )
        raise

    url: Optional[str] = None
    try:
        url = public_url_for(key)
    except Exception:  # pragma: no cover - configuration mismatch
        logger.exception("[poster-upload] Failed to build public URL", extra={"slot": slot})
        url = None

    byte_length = len(raw)
    declared_size = int(size) if isinstance(size, int) else None
    stored_size = declared_size if declared_size and declared_size > 0 else byte_length

    metadata = _read_metadata()
    metadata[slot] = {
        "filename": safe_filename,
        "content_type": content_type,
        "path": path.name,
        "width": width,
        "height": height,
        "key": key,
    }
    if stored_size:
        metadata[slot]["size"] = stored_size
    if url:
        metadata[slot]["url"] = url

    _write_metadata(metadata)
    logger.info("[poster-upload] Metadata updated", extra={"slot": slot})

    return TemplatePosterRecord(
        slot=slot,
        filename=safe_filename,
        content_type=content_type,
        path=path,
        width=width,
        height=height,
        key=key,
        url=url,
    )


def poster_entry_from_record(record: TemplatePosterRecord) -> dict[str, PosterImage]:
    return {"slot": record.slot, "poster": _poster_from_record(record)}


def list_poster_entries() -> list[dict[str, PosterImage]]:
    entries: list[dict[str, PosterImage]] = []
    for record in iter_template_records():
        entries.append(poster_entry_from_record(record))
    return entries


def generation_overrides(desired: int) -> list[PosterImage]:
    if desired < 1:
        return []
    records = list(iter_template_records())
    if desired < 2 or len(records) < 2:
        return []

    posters: List[PosterImage] = []
    for record in records:
        posters.append(_poster_from_record(record))

    if len(posters) >= desired:
        return posters[:desired]

    result: list[PosterImage] = posters[:]
    index = 0
    while len(result) < desired:
        source = posters[index % len(posters)]
        payload = {
            "filename": source.filename,
            "media_type": source.media_type,
            "data_url": source.data_url,
            "url": source.url,
            "width": source.width,
            "height": source.height,
        }
        if hasattr(PosterImage, "model_validate"):
            clone = PosterImage.model_validate(payload)
        else:
            clone = PosterImage(**payload)
        result.append(clone)
        index += 1
    return result


__all__ = [
    "TemplatePosterRecord",
    "list_template_posters",
    "list_poster_entries",
    "save_template_poster",
    "generation_overrides",
]
