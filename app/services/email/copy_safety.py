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

_POINT_PREFIX_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^(feature|highlight|benefit|selling point|key point)\s*[:\-]\s*",
        r"^(亮点|卖点|特点|优势)\s*[:：\-]\s*",
        r"^(now with|designed for|ideal for|perfect for)\s+",
    )
]

_POINT_TAIL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\s+(for busy [^.!,;]+)$",
        r"\s+(for everyday [^.!,;]+)$",
        r"\s+(for daily [^.!,;]+)$",
        r"\s+(for modern [^.!,;]+)$",
        r"\s+(with less [^.!,;]+)$",
        r"\s+(with confidence)$",
        r"\s+(made easy)$",
        r"\s+(after [^.!,;]+)$",
        r"\s+(so you can [^.!,;]+)$",
        r"\s+(to help [^.!,;]+)$",
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


def normalize_marketing_title(value: Any) -> str:
    text = sanitize_marketing_text(value)
    if not text:
        return ""
    text = re.sub(r"[!！?？]+$", "", text)
    text = re.sub(r"\s*[\-|/|]+\s*$", "", text)
    return clean_copy_text(text.strip(" -|:;,.，。"))


def normalize_marketing_subtitle(value: Any, *, title: str = "") -> str:
    text = sanitize_marketing_text(value)
    if not text:
        return ""
    for pattern in _POINT_PREFIX_PATTERNS:
        text = pattern.sub("", text)
    text = re.sub(r"[!！?？]+$", "", text)
    text = clean_copy_text(text.strip(" -|:;,.，。"))
    if title and text.casefold() == clean_copy_text(title).casefold():
        return ""
    return text


def compress_marketing_point(value: Any) -> str:
    text = sanitize_marketing_text(value)
    if not text:
        return ""
    for pattern in _POINT_PREFIX_PATTERNS:
        text = pattern.sub("", text)
    for pattern in _POINT_TAIL_PATTERNS:
        text = pattern.sub("", text)
    text = re.sub(r"\s*[|/]\s*.*$", "", text)
    text = clean_copy_text(text.strip(" -|:;,.，。"))
    return text


def sanitize_marketing_points(values: list[Any] | tuple[Any, ...] | None) -> list[str]:
    points: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        point = compress_marketing_point(value)
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
