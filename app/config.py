
# app/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


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

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)


@dataclass
class Settings:
    # 环境
    environment: str
    allowed_origins: List[str]

    # 邮件
    email: EmailConfig

    # Glibatree（可选）
    glibatree: GlibatreeConfig

    # OpenAI（用于生成图片）
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str
    openai_image_size: str


@lru_cache()
def get_settings() -> Settings:
    # 环境 / CORS
    environment = os.getenv("ENVIRONMENT", "development")
    # 兼容两种命名
    origins_raw = os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("ALLOWED_ORIGINS") or "*"
    allowed_origins = _as_list(origins_raw, ["*"])

    # 邮件（兼容两套变量名）
    email = EmailConfig(
        host=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS"),
        sender=os.getenv("EMAIL_SENDER") or os.getenv("FROM_EMAIL"),

        use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        use_ssl=_as_bool(os.getenv("SMTP_USE_SSL"), False),
    )


    # Glibatree（命名兼容）
    glibatree = GlibatreeConfig(
        api_url=os.getenv("GLIBATREE_API_URL") or os.getenv("GLIB_URL"),
        api_key=os.getenv("GLIBATREE_API_KEY") or os.getenv("GLIB_KEY"),
    )

    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")  # 为空则使用官方默认
    openai_model = os.getenv("OPENAI_MODEL", "gpt-image-1")
    openai_image_size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")

    return Settings(
        environment=environment,
        allowed_origins=allowed_origins,
        email=email,
        glibatree=glibatree,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_model=openai_model,
        openai_image_size=openai_image_size,
    )

