from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Request


OPS_USERNAME = "ops"

PROTECTED_API_PREFIXES = (
    "/api/r2/presign-put",
    "/api/template-posters",
    "/api/generate-slot-image",
    "/api/generate-poster",
    "/api/send-email",
    "/api/image/generate",
    "/api/imagen/generate",
    "/api/v2/",
    "/debug/vertex/",
)

PUBLIC_PATHS = {
    "/health",
    "/healthz",
    "/api/auth/ops-login",
    "/api/auth/logout",
    "/api/auth/me",
}


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalise_same_site(value: str | None) -> str:
    text = (value or "lax").strip().lower()
    if text not in {"lax", "strict", "none"}:
        return "lax"
    return text


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _urlsafe_b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(f"{text}{padding}")


@dataclass(frozen=True)
class OpsAuthSettings:
    enabled: bool
    password: str | None
    session_secret: str | None
    allowed_origin: str | None
    cookie_name: str
    cookie_max_age_sec: int
    cookie_secure: bool
    cookie_samesite: str

    @property
    def is_active(self) -> bool:
        return bool(self.enabled and self.password and self.session_secret)


def load_ops_auth_settings() -> OpsAuthSettings:
    return OpsAuthSettings(
        enabled=_as_bool(os.getenv("OPS_UI_ENABLED"), False),
        password=os.getenv("OPS_UI_PASSWORD"),
        session_secret=os.getenv("OPS_UI_SESSION_SECRET"),
        allowed_origin=(os.getenv("OPS_UI_ALLOWED_ORIGIN") or "").strip() or None,
        cookie_name=(os.getenv("OPS_UI_COOKIE_NAME") or "ops_ui_session").strip() or "ops_ui_session",
        cookie_max_age_sec=max(int(os.getenv("OPS_UI_COOKIE_MAX_AGE_SEC", "43200") or 43200), 1),
        cookie_secure=_as_bool(os.getenv("OPS_UI_COOKIE_SECURE"), True),
        cookie_samesite=_normalise_same_site(os.getenv("OPS_UI_COOKIE_SAMESITE")),
    )


def is_protected_api_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return False
    return any(path.startswith(prefix) for prefix in PROTECTED_API_PREFIXES)


def _sign_value(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def build_session_cookie(username: str, settings: OpsAuthSettings, now: int | None = None) -> str:
    issued_at = int(now or time.time())
    payload = {
        "sub": username,
        "iat": issued_at,
        "exp": issued_at + settings.cookie_max_age_sec,
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_token = _urlsafe_b64encode(payload_text.encode("utf-8"))
    signature = _sign_value(payload_token, settings.session_secret or "")
    return f"{payload_token}.{signature}"


def read_session_cookie(cookie_value: str | None, settings: OpsAuthSettings, now: int | None = None) -> dict[str, Any] | None:
    if not cookie_value or not settings.is_active:
        return None
    try:
        payload_token, signature = cookie_value.split(".", 1)
    except ValueError:
        return None
    expected = _sign_value(payload_token, settings.session_secret or "")
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_urlsafe_b64decode(payload_token).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("sub") != OPS_USERNAME:
        return None
    if int(payload.get("exp") or 0) <= int(now or time.time()):
        return None
    return payload


def is_authenticated(request: Request, settings: OpsAuthSettings | None = None) -> bool:
    auth_settings = settings or load_ops_auth_settings()
    if not auth_settings.is_active:
        return True
    cookie_value = request.cookies.get(auth_settings.cookie_name)
    return read_session_cookie(cookie_value, auth_settings) is not None


def auth_state(request: Request, settings: OpsAuthSettings | None = None) -> dict[str, Any]:
    auth_settings = settings or load_ops_auth_settings()
    authenticated = is_authenticated(request, auth_settings)
    return {
        "enabled": auth_settings.is_active,
        "authenticated": authenticated,
        "username": OPS_USERNAME if authenticated and auth_settings.is_active else None,
    }
