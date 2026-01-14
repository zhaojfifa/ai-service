from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Tuple

import requests

logger = logging.getLogger("ai_service.email_sender")

from app.config import get_settings
from app.schemas import PosterImage, SendEmailRequest, SendEmailResponse
from app.services.s3_client import public_url_for


def send_email(payload: SendEmailRequest) -> SendEmailResponse:
    settings = get_settings()

    if not settings.email.is_configured:
        logger.warning("SMTP not configured; skip sending email to %s", payload.recipient)
        return SendEmailResponse(
            status="skipped",
            detail="邮件服务未配置，只做预览。",
        )

    from_addr = settings.email.sender or settings.email.username
    if not from_addr:
        logger.warning("Missing from address while sending email to %s", payload.recipient)
        return SendEmailResponse(
            status="skipped",
            detail="缺少发件人邮箱配置。",
        )

    try:
        message = EmailMessage()
        message["To"] = payload.recipient
        message["From"] = from_addr
        message["Subject"] = payload.subject
        message.set_content(payload.body)

        if payload.attachment:
            filename, content, media_type = _decode_attachment(payload.attachment)
            maintype, subtype = media_type.split("/", 1)
            message.add_attachment(
                content, maintype=maintype, subtype=subtype, filename=filename
            )

        if settings.email.use_ssl:
            smtp = smtplib.SMTP_SSL(settings.email.host, settings.email.port, timeout=20)
        else:
            smtp = smtplib.SMTP(settings.email.host, settings.email.port, timeout=20)

        with smtp as server:
            server.ehlo()
            if settings.email.use_tls and not settings.email.use_ssl:
                server.starttls()
            if settings.email.username and settings.email.password:
                server.login(settings.email.username, settings.email.password)
            server.send_message(message)

        logger.info(
            "Email sent via SMTP host=%s port=%s tls=%s ssl=%s from=%s to=%s",
            settings.email.host,
            settings.email.port,
            settings.email.use_tls,
            settings.email.use_ssl,
            from_addr,
            payload.recipient,
        )
        return SendEmailResponse(status="sent", detail="邮件已发送。")
    except Exception as exc:  # pragma: no cover - runtime safety
        logger.exception("send_email_smtp failed")
        return SendEmailResponse(status="error", detail=f"发送失败: {exc}")


def _decode_attachment(attachment: PosterImage) -> Tuple[str, bytes, str]:
    if attachment.data_url:
        raise ValueError("Payload contains base64/data_url. Please provide assets by key/url only.")

    url = attachment.url
    if not url and attachment.key:
        url = public_url_for(attachment.key)

    if url and url.startswith(("r2://", "s3://")) and attachment.key:
        url = public_url_for(attachment.key)

    if url:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.content
        media_type = attachment.media_type or response.headers.get(
            "Content-Type", "application/octet-stream"
        )
    else:
        raise ValueError("Attachment missing url/key source")

    filename = attachment.filename or "poster.png"
    return filename, content, media_type

