from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_FAILURE_HTTP_STATUS = {
    "asset_fetch": 502,
    "image_decode": 422,
    "material_prepare": 422,
    "puppeteer_render": 502,
    "compose": 500,
    "storage_publish": 502,
}


@dataclass(frozen=True)
class StageFailureContext:
    stage: str
    code: str
    message: str
    exception_class: str
    detail: str | None = None
    asset_url: str | None = None
    content_type: str | None = None
    byte_size: int | None = None
    decoded_width: int | None = None
    decoded_height: int | None = None
    retryable: bool = False
    timeout_ms: int | None = None
    extra: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "stage": self.stage,
            "code": self.code,
            "message": self.message,
            "exception_class": self.exception_class,
            "detail": self.detail,
            "asset_url": self.asset_url,
            "content_type": self.content_type,
            "byte_size": self.byte_size,
            "decoded_width": self.decoded_width,
            "decoded_height": self.decoded_height,
            "retryable": self.retryable,
            "timeout_ms": self.timeout_ms,
            "extra": self.extra,
        }
        return {key: value for key, value in payload.items() if value is not None}


class PosterGenerationStageError(RuntimeError):
    def __init__(
        self,
        stage: str,
        code: str,
        message: str,
        *,
        detail: str | None = None,
        exception_class: str | None = None,
        asset_url: str | None = None,
        content_type: str | None = None,
        byte_size: int | None = None,
        decoded_width: int | None = None,
        decoded_height: int | None = None,
        retryable: bool = False,
        timeout_ms: int | None = None,
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.context = StageFailureContext(
            stage=stage,
            code=code,
            message=message,
            detail=detail,
            exception_class=exception_class or self.__class__.__name__,
            asset_url=asset_url,
            content_type=content_type,
            byte_size=byte_size,
            decoded_width=decoded_width,
            decoded_height=decoded_height,
            retryable=retryable,
            timeout_ms=timeout_ms,
            extra=extra,
        )
        self.stage = stage
        self.code = code
        self.detail = detail or message
        self.reason_code = code

    @property
    def status_code(self) -> int:
        return _FAILURE_HTTP_STATUS.get(self.stage, 500)

    def as_dict(self) -> dict[str, Any]:
        return self.context.as_dict()


def failure_response_payload(
    *,
    error: PosterGenerationStageError,
    request_id: str | None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "poster2_generation_failed",
        "request_id": request_id,
        "failure": error.as_dict(),
    }
