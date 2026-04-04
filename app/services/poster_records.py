from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.r2_client import get_bytes, put_bytes


POSTER_RECORD_PREFIX = "poster-records"
POSTER_RECORD_DIR = Path("/tmp/ai-service/poster-records")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_poster_key() -> str:
    return f"p2_{uuid.uuid4().hex[:16]}"


def _storage_key(poster_key: str) -> str:
    return f"{POSTER_RECORD_PREFIX}/{poster_key}.json"


def _local_path(poster_key: str) -> Path:
    return POSTER_RECORD_DIR / f"{poster_key}.json"


def _write_local_record(poster_key: str, record: dict[str, Any]) -> None:
    path = _local_path(poster_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_local_record(poster_key: str) -> dict[str, Any] | None:
    path = _local_path(poster_key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_poster_record(record: dict[str, Any]) -> dict[str, Any]:
    poster_key = str(record["poster_key"])
    payload = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
    try:
        url = put_bytes(_storage_key(poster_key), payload, content_type="application/json")
    except Exception:
        url = None
    if not url:
        _write_local_record(poster_key, record)
    return record


def load_poster_record(poster_key: str) -> dict[str, Any] | None:
    try:
        raw = get_bytes(_storage_key(poster_key))
    except Exception:
        return _read_local_record(poster_key)
    return json.loads(raw.decode("utf-8"))


def create_poster_record(
    *,
    poster_key: str,
    request_snapshot: dict[str, Any],
    render_result: dict[str, Any],
    final_poster: dict[str, Any],
) -> dict[str, Any]:
    now = _utc_now()
    record = {
        "poster_key": poster_key,
        "created_at": now,
        "updated_at": now,
        "template_id": render_result.get("template_id") or request_snapshot.get("template_id") or "template_dual_v2",
        "trace_id": render_result.get("trace_id") or "",
        "final_hash": render_result.get("final_hash") or "",
        "final_poster": deepcopy(final_poster),
        "request_snapshot": deepcopy(request_snapshot),
        "render_result": deepcopy(render_result),
        "email_draft": None,
        "email_deliveries": [],
    }
    return save_poster_record(record)


def update_email_draft(poster_key: str, draft: dict[str, Any]) -> dict[str, Any]:
    record = load_poster_record(poster_key)
    if record is None:
        raise KeyError(poster_key)
    record["email_draft"] = deepcopy(draft)
    record["updated_at"] = _utc_now()
    return save_poster_record(record)


def append_email_delivery(poster_key: str, delivery: dict[str, Any], draft: dict[str, Any] | None = None) -> dict[str, Any]:
    record = load_poster_record(poster_key)
    if record is None:
        raise KeyError(poster_key)
    deliveries = list(record.get("email_deliveries") or [])
    deliveries.append(deepcopy(delivery))
    record["email_deliveries"] = deliveries
    if draft is not None:
        record["email_draft"] = deepcopy(draft)
    record["updated_at"] = _utc_now()
    return save_poster_record(record)
