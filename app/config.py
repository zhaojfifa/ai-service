from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List
from urllib.parse import urlparse


def _as_bool(value: str | None, default: bool) -> bool:
    """Interpret common truthy / falsy strings while providing a default."""

    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}



def _as_list(csv: str | None, fallback: List[str]) -> List[str]:
    if not csv:
        return fallback
    items = [x.strip() for x in csv.split(",") if x.strip()]
    return items or fallback

@dataclass
class EmailConfig:
    host: str | None
    port: int
    username: str | None
    password: str | None
    sender: str | None
    use_tls: bool
    use_ssl: bool

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.sender)


@dataclass
class GlibatreeConfig:
    api_url: str | None
    api_key: str | None
    model: str | None
    proxy: str | None
    client: str

    @property
    def use_openai_client(self) -> bool:
        return self.client == "openai"

    @property
    def is_configured(self) -> bool:
        if self.use_openai_client:
            return bool(self.api_key)
        return bool(self.api_url and self.api_key)


@dataclass
class Settings:
    environment: str
    allowed_origins: List[str]
    email: EmailConfig
    glibatree: GlibatreeConfig


def _parse_allowed_origins(raw: str) -> List[str]:
    """Normalise comma-separated origins into values accepted by CORSMiddleware."""

    if not raw:
        return ["*"]

    cleaned: List[str] = []
    for origin in raw.split(","):
        value = origin.strip()
        if not value:
            continue
        if value == "*":
            return ["*"]

        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            normalised = f"{parsed.scheme}://{parsed.netloc}"
        else:
            normalised = value

        if normalised not in cleaned:
            cleaned.append(normalised)

@lru_cache()
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
    allowed_origins = _parse_allowed_origins(origins_raw)

    email = EmailConfig(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        sender=os.getenv("EMAIL_SENDER"),
        use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        use_ssl=_as_bool(os.getenv("SMTP_USE_SSL"), False),
    )

    api_url = os.getenv("GLIBATREE_API_URL")
    raw_client = os.getenv("GLIBATREE_CLIENT")
    if raw_client:
        client = raw_client.strip().lower()
        if client not in {"http", "openai"}:
            client = "openai" if (api_url and "openai" in api_url.lower()) else "http"
    elif api_url and "openai" in api_url.lower():
        client = "openai"
    elif api_url:
        client = "http"
    else:
        client = "openai"

    glibatree = GlibatreeConfig(
        api_url=api_url,
        api_key=os.getenv("GLIBATREE_API_KEY"),
        model=os.getenv("GLIBATREE_MODEL", "gpt-image-1"),
        proxy=os.getenv("GLIBATREE_PROXY"),
        client=client,
    )

    return Settings(
        environment=environment,
        allowed_origins=allowed_origins,
        email=email,
        glibatree=glibatree,
    )

