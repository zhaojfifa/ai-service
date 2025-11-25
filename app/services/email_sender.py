from __future__ import annotations

import base64
import smtplib
from email.message import EmailMessage
from typing import Tuple

import requests
from loguru import logger

from app.config import get_settings
from app.schemas import PosterImage, SendEmailRequest, SendEmailResponse


def send_email(payload: SendEmailRequest) -> SendEmailResponse:
    settings = get_settings()

    if not settings.email.is_configured:
        return SendEmailResponse(
            status="skipped",
            detail="邮件服务未配置，只做预览。",
        )

    from_addr = settings.email.sender or settings.email.username
    if not from_addr:
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

        return SendEmailResponse(status="sent", detail="邮件已发送。")
    except Exception as exc:  # pragma: no cover - runtime safety
        logger.exception("send_email_smtp failed")
        return SendEmailResponse(status="error", detail=f"发送失败: {exc}")


def _decode_attachment(attachment: PosterImage) -> Tuple[str, bytes, str]:
    if attachment.data_url:
        header, encoded = attachment.data_url.split(",", 1)
        if not header.startswith("data:") or ";base64" not in header:
            raise ValueError("Attachment must be provided as base64 data URL")
        media_type = header[len("data:"): header.index(";")]
        content = base64.b64decode(encoded)
    elif attachment.url:
        response = requests.get(attachment.url, timeout=30)
        response.raise_for_status()
        content = response.content
        media_type = attachment.media_type or response.headers.get(
            "Content-Type", "application/octet-stream"
        )
    else:
        raise ValueError("Attachment missing data_url or URL source")

    filename = attachment.filename or "poster.png"
    return filename, content, media_type

