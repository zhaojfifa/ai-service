from app import config as config_module
from app.config import _parse_allowed_origins


def test_parse_allowed_origins_with_paths() -> None:
    raw = "https://example.com/app, https://demo.com/sub"
    assert _parse_allowed_origins(raw) == [
        "https://example.com",
        "https://demo.com",
    ]


def test_parse_allowed_origins_with_wildcard() -> None:
    assert _parse_allowed_origins("*") == ["*"]


def test_parse_allowed_origins_deduplicates_and_handles_empty() -> None:
    raw = " https://example.com/ , https://example.com ,"
    assert _parse_allowed_origins(raw) == ["https://example.com"]


def test_parse_allowed_origins_defaults_to_wildcard() -> None:
    assert _parse_allowed_origins("") == ["*"]


def test_get_settings_uses_cors_allowed_origins_alias(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://ops.example.com/app")
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    config_module.get_settings.cache_clear()
    try:
        settings = config_module.get_settings()
    finally:
        config_module.get_settings.cache_clear()
    assert settings.allowed_origins == ["https://ops.example.com"]
