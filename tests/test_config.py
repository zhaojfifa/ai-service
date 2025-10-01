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
