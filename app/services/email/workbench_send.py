"""CUISTANCE commercial trial — PR-4 manual multi-recipient send helpers.

Pure helpers only (no provider calls, no app.main import): validate + deduplicate manually-entered recipients.
The send loop + evidence persistence live in the endpoint, reusing the existing email provider path and the
deterministic PR-3S email package (never reconstructing the body).

Manual recipients ONLY: no contact import, no Excel, no CRM, no scheduling, no segmentation, no analytics.
"""
from __future__ import annotations

import re
from typing import Any

# Pragmatic email shape check (matches the spirit of EmailStr without rejecting the whole batch).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(address: str) -> bool:
    addr = (address or "").strip()
    return bool(addr) and _EMAIL_RE.match(addr) is not None and len(addr) <= 254


def normalize_recipients(recipients: list[str] | None) -> dict[str, Any]:
    """Deterministic handling: trim, drop empties, deduplicate (order-preserving, case-insensitive),
    and split into valid vs invalid. Prefers unique recipients for safety.

    Returns: {unique, valid, invalid, deduplicated_count, total_input}
    """
    raw = [str(r).strip() for r in (recipients or []) if str(r).strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for addr in raw:
        fold = addr.casefold()
        if fold in seen:
            continue
        seen.add(fold)
        unique.append(addr)
    valid = [a for a in unique if is_valid_email(a)]
    invalid = [a for a in unique if not is_valid_email(a)]
    return {
        "unique": unique,
        "valid": valid,
        "invalid": invalid,
        "deduplicated_count": len(raw) - len(unique),
        "total_input": len(raw),
    }


__all__ = ["is_valid_email", "normalize_recipients"]
