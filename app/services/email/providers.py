from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider: str
    status: str
    provider_message_id: str | None = None
    error: str | None = None


class EmailProvider(Protocol):
    name: str

    def send(
        self,
        *,
        recipient: str,
        subject: str,
        preview_text: str,
        html: str,
        text: str,
    ) -> EmailDeliveryResult:
        ...


class InlineOnlyEmailProvider:
    name = "inline_only"

    def send(
        self,
        *,
        recipient: str,
        subject: str,
        preview_text: str,
        html: str,
        text: str,
    ) -> EmailDeliveryResult:
        return EmailDeliveryResult(provider=self.name, status="preview_only")


def get_email_provider(delivery_mode: str) -> EmailProvider:
    if delivery_mode == "inline_only":
        return InlineOnlyEmailProvider()

    if delivery_mode == "resend":
        from app.services.email.resend_provider import ResendEmailProvider

        settings = get_settings()
        return ResendEmailProvider(settings.resend)

    raise ValueError(f"Unsupported delivery_mode: {delivery_mode}")
