from __future__ import annotations

import requests

from app.config import ResendConfig
from app.services.email.providers import EmailDeliveryResult


class ResendEmailProvider:
    name = "resend"

    def __init__(self, config: ResendConfig) -> None:
        self._config = config

    def send(
        self,
        *,
        recipient: str,
        subject: str,
        preview_text: str,
        html: str,
        text: str,
    ) -> EmailDeliveryResult:
        if not self._config.is_configured:
            return EmailDeliveryResult(
                provider=self.name,
                status="error",
                error="Resend is not configured.",
            )

        payload = {
            "from": self._config.from_email,
            "to": [recipient],
            "subject": subject,
            "html": html,
            "text": text,
        }
        if self._config.audience:
            payload["tags"] = [{"name": "audience", "value": self._config.audience}]

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - runtime safety
            return EmailDeliveryResult(
                provider=self.name,
                status="error",
                error=str(exc),
            )

        return EmailDeliveryResult(
            provider=self.name,
            status="sent",
            provider_message_id=data.get("id"),
        )
