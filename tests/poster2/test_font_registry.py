from __future__ import annotations

import os
from pathlib import Path

from app.services.poster2.font_registry import FontRegistry, get_poster2_fonts_dir


def test_font_preflight_reports_missing_fonts(tmp_path: Path):
    registry = FontRegistry(tmp_path)
    payload = registry.preflight()

    assert payload["ready"] is False
    assert payload["using_pil_default"] is True
    assert payload["required_fonts"]["brand_regular"]["exists"] is False
    assert payload["required_fonts"]["brand_bold"]["exists"] is False


def test_font_preflight_reports_real_files_as_readable(tmp_path: Path):
    regular = tmp_path / "NotoSansSC-Regular.ttf"
    semibold = tmp_path / "NotoSansSC-SemiBold.ttf"
    regular.write_bytes(b"not-a-real-font")
    semibold.write_bytes(b"not-a-real-font")

    registry = FontRegistry(tmp_path)
    payload = registry.preflight()

    assert payload["required_fonts"]["brand_regular"]["exists"] is True
    assert payload["required_fonts"]["brand_regular"]["readable"] is True
    assert payload["required_fonts"]["brand_regular"]["loadable"] is False
    assert payload["ready"] is False


def test_get_poster2_fonts_dir_resolves_relative_env_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("POSTER2_FONT_DIR", "app/assets/fonts")
    resolved = get_poster2_fonts_dir()

    assert resolved.is_absolute()
    assert str(resolved).endswith(os.path.join("app", "assets", "fonts"))
