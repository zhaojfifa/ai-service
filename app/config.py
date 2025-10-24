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
    """Split a CSV string to list with trimming and fallback."""
    if not csv:
        return fallback
    items = [x.strip() for x in csv.split(",") if x.strip()]
    return items or fallback


def _normalise_origin(value: str) -> str | None:
    """
    将单个 origin 归一化：
    - 允许 "*"
    - 允许裸域名（如 localhost:5173），自动补 http://
    - 去掉路径，仅保留 scheme://host[:port]
    - 非法值返回 None
    """
    v = value.strip()
    if not v:
        return None
    if v == "*":
        return "*"
    if "://" not in v:
        # 浏览器 Origin 一定包含 scheme；为了容错，这里自动补 http
        v = "http://" + v
    p = urlparse(v)
    if not (p.scheme and p.netloc):
        return None
    return f"{p.scheme}://{p.netloc}"


def _parse_allowed_origins(raw: str | None) -> List[str]:
    """
    解析 ALLOWED_ORIGINS 环境变量，返回始终非空的 list[str]。
    支持: "*", 逗号分隔、去重、自动补 scheme、去除路径。
    """
    if not raw:
        return ["*"]

    cleaned: List[str] = []
    for token in raw.split(","):
        origin = _normalise_origin(token)
        if origin == "*":
            return ["*"]
        if origin and origin not in cleaned:
            cleaned.append(origin)

    return cleaned or ["*"]

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
class GCPConfig:
    project_id: str | None
    location: str = "us-central1"

    @property
    def is_configured(self) -> bool:
        return bool(self.project_id)


@dataclass
class VertexConfig:
    imagen_generate_model: str = "imagen-3.0-generate-001"


@dataclass
class GuardConfig:
    max_body_bytes: int
    disallow_base64: bool

    @classmethod
    def from_env(cls) -> "GuardConfig":
        raw_max = os.getenv("UPLOAD_MAX_BYTES", "4194304")
        try:
            max_bytes = max(int(raw_max), 0)
        except (TypeError, ValueError):
            max_bytes = 4 * 1024 * 1024

        disallow_raw = os.getenv("DISALLOW_BASE64_IN_JSON", "true")
        disallow = str(disallow_raw).strip().lower() in {"1", "true", "yes", "on"}
        return cls(max_body_bytes=max_bytes, disallow_base64=disallow)


@dataclass
class OpenAIConfig:
    api_key: str | None = None
    base_url: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)


@dataclass
class GlibatreeConfig:
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    proxy: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    @classmethod
    def from_env(cls) -> "GlibatreeConfig":
        api_key = os.getenv("GLIBATREE_API_KEY") or os.getenv("OPENAI_API_KEY")
        api_url = os.getenv("GLIBATREE_API_URL") or os.getenv("GLIBATREE_BASE_URL")
        model = os.getenv("GLIBATREE_MODEL") or os.getenv("OPENAI_MODEL")
        proxy = os.getenv("GLIBATREE_PROXY") or os.getenv("OPENAI_PROXY")

        if not api_url:
            api_url = os.getenv("OPENAI_BASE_URL")

        return cls(api_url=api_url, api_key=api_key, model=model, proxy=proxy)


@dataclass
class Settings:
    environment: str
    allowed_origins: List[str]
    email: EmailConfig
    gcp: GCPConfig
    vertex: VertexConfig
    guard: GuardConfig
    glibatree: GlibatreeConfig
    openai: OpenAIConfig
    s3_endpoint: str | None
    s3_access_key: str | None
    s3_secret_key: str | None
    s3_region: str
    s3_bucket: str | None
    s3_public_base: str | None


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

    return cleaned or ["*"]


@lru_cache()
def get_settings() -> Settings:
    def _get(name: str, default: str | None = None) -> str | None:
        v = os.getenv(name)
        return v if v is not None else default

    def _truthy(v: str | None) -> bool:
        return str(v).strip().lower() in {"1", "true", "yes", "on"}

    environment = _get("ENVIRONMENT", "development")
    origins_raw = _get("ALLOWED_ORIGINS", "*")
    allowed_origins = _parse_allowed_origins(origins_raw)

    email = EmailConfig(
        host=_get("SMTP_HOST"),
        port=int(_get("SMTP_PORT", "587")),
        username=_get("SMTP_USERNAME"),
        password=_get("SMTP_PASSWORD"),
        sender=_get("EMAIL_SENDER"),
        use_tls=_as_bool(_get("SMTP_USE_TLS"), True),
        use_ssl=_as_bool(_get("SMTP_USE_SSL"), False),
    )

    gcp = GCPConfig(
        project_id=_get("GCP_PROJECT_ID"),
        location=_get("GCP_LOCATION", "us-central1") or "us-central1",
    )

    vertex = VertexConfig(
        imagen_generate_model=_get("VERTEX_IMAGEN_GENERATE_MODEL", "imagen-3.0-generate-001")
        or "imagen-3.0-generate-001",
    )

    guard = GuardConfig.from_env()

    openai_cfg = OpenAIConfig(
        api_key=_get("OPENAI_API_KEY"),
        base_url=_get("OPENAI_BASE_URL"),
    )

    glibatree = GlibatreeConfig.from_env()

    return Settings(
        environment=environment,
        allowed_origins=allowed_origins,
        email=email,
        gcp=gcp,
        vertex=vertex,
        guard=guard,
        glibatree=glibatree,
        openai=openai_cfg,
        s3_endpoint=_get("S3_ENDPOINT"),
        s3_access_key=_get("S3_ACCESS_KEY"),
        s3_secret_key=_get("S3_SECRET_KEY"),
        s3_region=_get("S3_REGION", "auto"),
        s3_bucket=_get("S3_BUCKET"),
        s3_public_base=_get("S3_PUBLIC_BASE"),
    )

