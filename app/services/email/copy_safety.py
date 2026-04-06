from __future__ import annotations

import re
from typing import Any


_PROMPT_LIKE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bignore\s+(all\s+)?previous\s+instructions\b",
        r"\bsystem\s+prompt\b",
        r"\bdeveloper\s+prompt\b",
        r"\btraining\s+data\b",
        r"\bfor\s+internal\s+use\b",
        r"\binternal\s+only\b",
        r"\bcopilot\b",
        r"\bchatgpt\b",
        r"\bopenai\b",
        r"\banthropic\b",
        r"\bclaude\b",
        r"\bgemini\b",
        r"\bllm\b",
        r"\bprompt\s*:\b",
        r"\buser\s*:\b",
        r"\bassistant\s*:\b",
        r"\bmodel\s+instruction\b",
        r"\blorem\s+ipsum\b",
        r"\bplaceholder\b",
    )
]

_UNGROUNDED_CLAIM_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\$\s?\d",
        r"\b\d+%\s+off\b",
        r"\bfree\s+shipping\b",
        r"\bnext[-\s]?day\s+delivery\b",
        r"\bdelivery\s+guarantee\b",
        r"\bships?\s+(today|tomorrow|same\s+day)\b",
        r"\b(certified|certification)\b",
        r"\bUL\b",
        r"\bETL\b",
        r"\bCE\b",
        r"\bNSF\b",
        r"\bFDA\b",
        r"\bwarranty\b",
        r"\blifetime\b",
        r"\bguarantee\b",
    )
]


def clean_copy_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def _is_prompt_like(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PROMPT_LIKE_PATTERNS)


def sanitize_marketing_text(value: Any) -> str:
    text = clean_copy_text(value)
    if not text:
        return ""

    text = re.sub(r"(?i)\b(subject|preview|summary|title|subtitle|text|html)\s*:\s*", "", text)
    segments = re.split(r"[\r\n]+|(?<=[.!?;])\s+", text)
    kept = [segment.strip(" -|•\t") for segment in segments if segment.strip() and not _is_prompt_like(segment)]
    if not kept:
        return ""

    sanitized = clean_copy_text(" ".join(kept)).strip(" -|•")
    if not sanitized or _is_prompt_like(sanitized):
        return ""
    return sanitized


def sanitize_marketing_points(values: list[Any] | tuple[Any, ...] | None) -> list[str]:
    points: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        point = sanitize_marketing_text(value)
        if not point:
            continue
        point = point.rstrip(".;,:")
        key = point.casefold()
        if key in seen:
            continue
        seen.add(key)
        points.append(point)
    return points


def build_grounded_fact_blob(canonical_input: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("brand_name", "agent_name", "title", "subtitle", "final_poster_url"):
        value = sanitize_marketing_text(canonical_input.get(key))
        if value:
            parts.append(value)
    parts.extend(sanitize_marketing_points(canonical_input.get("summary_points") or []))
    return " ".join(parts)


def contains_ungrounded_claims(text: str, canonical_input: dict[str, Any]) -> bool:
    clean = sanitize_marketing_text(text)
    if not clean:
        return False
    grounded = build_grounded_fact_blob(canonical_input).casefold()
    for pattern in _UNGROUNDED_CLAIM_PATTERNS:
        match = pattern.search(clean)
        if match and match.group(0).casefold() not in grounded:
            return True
    return False
