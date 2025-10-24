"""Cloudflare R2 helper utilities with backward compatibility."""
from __future__ import annotations

import datetime as _dt
import os
import re
import uuid
from functools import lru_cache
from typing import Optional

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError


def _env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        text = value.strip()
        if text:
            return text
    return None


@lru_cache(maxsize=1)
def _session() -> boto3.session.Session:
    return boto3.session.Session()


@lru_cache(maxsize=1)
def _client() -> BaseClient:
    endpoint = _env("R2_ENDPOINT", "S3_ENDPOINT")
    access = _env("R2_ACCESS_KEY_ID", "S3_ACCESS_KEY")
    secret = _env("R2_SECRET_ACCESS_KEY", "S3_SECRET_KEY")
    region = _env("R2_REGION", "S3_REGION") or "auto"
    if not (endpoint and access and secret):
        raise RuntimeError("R2 storage is not configured")
    return _session().client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region,
    )


def get_client() -> BaseClient:
    """Return the cached boto3 client for Cloudflare R2."""

    return _client()


def make_key(folder: str, filename: str) -> str:
    folder = (folder or "uploads").strip("/ ") or "uploads"
    date_part = _dt.datetime.utcnow().strftime("%Y%m%d")
    safe_name = re.sub(r"[^0-9A-Za-z._-]", "_", filename or "asset")
    return f"{folder}/{date_part}/{uuid.uuid4().hex}/{safe_name}"


def public_url_for(key: str) -> str | None:
    base = _env("R2_PUBLIC_BASE", "S3_PUBLIC_BASE")
    if not base:
        return None
    return f"{base.rstrip('/')}/{key.lstrip('/')}"


def presign_put_url(key: str, content_type: str, expires: int = 900) -> str:
    client = _client()
    bucket = _env("R2_BUCKET", "S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    try:
        return client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=max(int(expires), 60),
            HttpMethod="PUT",
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Failed to generate upload URL") from exc


def presign_put(key: str, content_type: str, expires: int = 900) -> str:
    """Alias used by some callers expecting a shorter function name."""

    return presign_put_url(key, content_type, expires)


def presign_get_url(key: str, expires: int | None = None) -> str:
    client = _client()
    bucket = _env("R2_BUCKET", "S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    ttl_raw = _env("R2_SIGNED_GET_TTL", "S3_SIGNED_GET_TTL")
    ttl = int(ttl_raw) if (ttl_raw and ttl_raw.isdigit()) else 0
    ttl = expires or ttl or 900
    try:
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=max(int(ttl), 60),
            HttpMethod="GET",
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Failed to generate download URL") from exc


def get_bytes(key: str) -> bytes:
    client = _client()
    bucket = _env("R2_BUCKET", "S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to fetch object {key}") from exc
    body = response.get("Body")
    if body is None:
        raise RuntimeError(f"Object {key} has no body")
    return body.read()


def put_bytes(key: str, data: bytes, *, content_type: str = "application/octet-stream") -> Optional[str]:
    client = _client()
    bucket = _env("R2_BUCKET", "S3_BUCKET")
    if not (client and bucket):
        return None
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    except (ClientError, BotoCoreError) as exc:
        import logging

        logging.getLogger(__name__).warning(
            "R2 put failed: bucket=%s key=%s err=%s", bucket, key, exc
        )
        return None

    return public_url_for(key)


__all__ = [
    "get_client",
    "make_key",
    "public_url_for",
    "presign_put_url",
    "presign_put",
    "presign_get_url",
    "get_bytes",
    "put_bytes",
]
