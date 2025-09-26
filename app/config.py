from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


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

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)


@dataclass
class Settings:
    environment: str
    allowed_origins: List[str]
    email: EmailConfig
    glibatree: GlibatreeConfig


@lru_cache()
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
    allowed_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]

    email = EmailConfig(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        sender=os.getenv("EMAIL_SENDER"),
        use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
    )

    glibatree = GlibatreeConfig(
        api_url=os.getenv("GLIBATREE_API_URL"),
        api_key=os.getenv("GLIBATREE_API_KEY"),
    )

    return Settings(
        environment=environment,
        allowed_origins=allowed_origins if allowed_origins else ["*"],
        email=email,
        glibatree=glibatree,
    )

