"""Compatibility shim：沿用旧路径导入新的 RejectHugeOrBase64 中间件。"""
from __future__ import annotations

from .reject_huge_or_base64 import RejectHugeOrBase64

__all__ = ["RejectHugeOrBase64"]
