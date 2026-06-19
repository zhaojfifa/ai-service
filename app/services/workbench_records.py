"""CUISTANCE commercial trial — PR-1 backend-owned workbench truth store.

Mirrors the poster_records storage pattern (R2 JSON object + /tmp fallback). Holds the lightweight
workbench/trial-campaign truth: product_truth, product_assets, email_banner — plus inert PR-2…PR-4
placeholders. URL/key references only; no binary/base64 is ever stored here.
"""
from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.r2_client import get_bytes, put_bytes


WORKBENCH_RECORD_PREFIX = "workbench-records"
WORKBENCH_RECORD_DIR = Path("/tmp/ai-service/workbench-records")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_workbench_key() -> str:
    return f"wb_{uuid.uuid4().hex[:16]}"


def _storage_key(workbench_key: str) -> str:
    return f"{WORKBENCH_RECORD_PREFIX}/{workbench_key}.json"


def _local_path(workbench_key: str) -> Path:
    return WORKBENCH_RECORD_DIR / f"{workbench_key}.json"


def _write_local_record(workbench_key: str, record: dict[str, Any]) -> None:
    path = _local_path(workbench_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_local_record(workbench_key: str) -> dict[str, Any] | None:
    path = _local_path(workbench_key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_workbench_record(record: dict[str, Any]) -> dict[str, Any]:
    workbench_key = str(record["workbench_key"])
    payload = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
    try:
        url = put_bytes(_storage_key(workbench_key), payload, content_type="application/json")
    except Exception:
        url = None
    if not url:
        _write_local_record(workbench_key, record)
    return record


def load_workbench_record(workbench_key: str) -> dict[str, Any] | None:
    try:
        raw = get_bytes(_storage_key(workbench_key))
    except Exception:
        return _read_local_record(workbench_key)
    return json.loads(raw.decode("utf-8"))


def create_workbench_record(
    *,
    workbench_key: str,
    language: str = "zh",
    status: str = "draft",
    product_truth: dict[str, Any] | None = None,
    product_assets: dict[str, Any] | None = None,
    email_banner: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    record = {
        "workbench_key": workbench_key,
        "created_at": now,
        "updated_at": now,
        "language": language,
        "status": status,
        "product_truth": deepcopy(product_truth or {}),
        "product_assets": deepcopy(product_assets or {}),
        "email_banner": deepcopy(email_banner or {}),
        # PR-2…PR-4 placeholders — inert in PR-1
        "poster_candidates": {},
        "selected_email_body_visual": None,
        "email_package_ref": None,
        "recipients": [],
        "send_attempts": [],
    }
    return save_workbench_record(record)


# fields a PATCH may replace in PR-1 (placeholders are owned by later PRs)
_PATCHABLE_FIELDS = ("language", "status", "product_truth", "product_assets", "email_banner")


def update_workbench_record(workbench_key: str, updates: dict[str, Any]) -> dict[str, Any]:
    record = load_workbench_record(workbench_key)
    if record is None:
        raise KeyError(workbench_key)
    for field in _PATCHABLE_FIELDS:
        if field in updates and updates[field] is not None:
            record[field] = deepcopy(updates[field])
    record["updated_at"] = _utc_now()
    return save_workbench_record(record)


# ---------------------------------------------------------------------------
# PR-2 — Step 2 candidate references + selected visual.
# Workbench stores ONLY a poster_key reference + a lightweight summary; the candidate truth lives in the
# poster_record (never copied here).
# ---------------------------------------------------------------------------

def set_poster_candidate(
    workbench_key: str,
    candidate_type: str,
    *,
    poster_key: str | None,
    status: str,
    template_id: str | None = None,
    contract_review_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store/refresh a candidate reference. (Re)generating the candidate that is currently selected resets
    selected_email_body_visual to None (no version history; scalar selection)."""
    record = load_workbench_record(workbench_key)
    if record is None:
        raise KeyError(workbench_key)
    candidates = dict(record.get("poster_candidates") or {})
    candidates[candidate_type] = {
        "poster_key": poster_key,
        "status": status,
        "generated_at": _utc_now(),
        "template_id": template_id,
        "contract_review_summary": deepcopy(contract_review_summary or {}),
    }
    record["poster_candidates"] = candidates
    if record.get("selected_email_body_visual") == candidate_type:
        # regenerating the selected candidate clears the selection
        record["selected_email_body_visual"] = None
    record["updated_at"] = _utc_now()
    return save_workbench_record(record)


def select_email_body_visual(workbench_key: str, candidate_type: str) -> dict[str, Any]:
    """Persist exactly one selected visual. A candidate must be ready; it must carry a poster_key UNLESS it is a
    deterministic workbench-truth product sheet (fiche / product_sheet_email — no poster generation, no poster_key)."""
    record = load_workbench_record(workbench_key)
    if record is None:
        raise KeyError(workbench_key)
    candidate = (record.get("poster_candidates") or {}).get(candidate_type) or {}
    if candidate.get("status") != "ready":
        raise ValueError("candidate_not_ready")
    summary = candidate.get("contract_review_summary") or {}
    is_workbench_truth_sheet = summary.get("generated_from") == "workbench_truth"
    if not candidate.get("poster_key") and not is_workbench_truth_sheet:
        raise ValueError("candidate_not_ready")
    record["selected_email_body_visual"] = candidate_type
    record["updated_at"] = _utc_now()
    return save_workbench_record(record)


# ---------------------------------------------------------------------------
# PR-4 — manual multi-recipient send evidence.
# ---------------------------------------------------------------------------

def append_send_attempts(
    workbench_key: str,
    attempts: list[dict[str, Any]],
    *,
    mark_sent: bool = False,
) -> dict[str, Any]:
    """Append per-recipient send attempts to the workbench evidence trail. Never stores provider secrets."""
    record = load_workbench_record(workbench_key)
    if record is None:
        raise KeyError(workbench_key)
    existing = list(record.get("send_attempts") or [])
    existing.extend(deepcopy(a) for a in attempts)
    record["send_attempts"] = existing
    if mark_sent:
        record["status"] = "sent"
    record["updated_at"] = _utc_now()
    return save_workbench_record(record)
