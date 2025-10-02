#!/usr/bin/env python3
"""Decode base64-encoded template assets into PNG files.

This script scans ``frontend/templates`` for ``*.b64`` files and writes
PNG files with the same basename. Existing PNGs are overwritten so the
script can be re-run safely.
"""
from __future__ import annotations

import base64
import pathlib


def decode_templates(root: pathlib.Path) -> None:
    template_dir = root / "frontend" / "templates"
    for b64_path in template_dir.glob("*.b64"):
        target = b64_path.with_suffix(".png")
        data = base64.b64decode(b64_path.read_text())
        target.write_bytes(data)
        print(f"Decoded {b64_path.name} -> {target.name}")


def main() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    decode_templates(repo_root)


if __name__ == "__main__":
    main()
