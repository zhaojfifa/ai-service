from __future__ import annotations

import datetime as _dt
import os
import re
import uuid
from functools import lru_cache
from typing import Optional
from urllib.parse import quote

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError


def _env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@lru_cache(maxsize=1)
def _session() -> boto3.session.Session:
    return boto3.session.Session()


def _client() -> BaseClient | None:
    endpoint = _env("S3_ENDPOINT")
    access_key = _env("S3_ACCESS_KEY")
    secret_key = _env("S3_SECRET_KEY")
    region = _env("S3_REGION") or "auto"
    if not (endpoint and access_key and secret_key):
        return None
    try:
        return _session().client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
    except Exception:
        return None


def get_client() -> BaseClient | None:
    """Return a cached boto3 client when credentials are available."""

    return _client()


def make_key(folder: str, filename: str) -> str:
    folder = (folder or "uploads").strip("/ ") or "uploads"
    date_part = _dt.datetime.utcnow().strftime("%Y%m%d")
    safe_name = re.sub(r"[^0-9A-Za-z._-]", "_", filename or "asset")
    return f"{folder}/{date_part}/{uuid.uuid4().hex}/{safe_name}"


def public_url_for(key: str) -> str | None:
    base = os.getenv("S3_PUBLIC_BASE")  # 必填：用 r2.dev 或自定义域
    if base:
        return f"{base.rstrip('/')}/{key}"
    # 没配就返回 None（不要拼 S3_ENDPOINT），避免给出不可用直链
    return None

def presigned_put_url(key: str, content_type: str, expires: int = 900) -> str:
    client = _client()
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    try:
        return client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=max(int(expires), 60),
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Failed to generate upload URL") from exc


def presigned_get_url(key: str, expires: int | None = None) -> str:
    client = _client()
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    ttl = expires
    if ttl is None:
        ttl_raw = _env("S3_SIGNED_GET_TTL")
        ttl = int(ttl_raw) if ttl_raw and ttl_raw.isdigit() else 0
    ttl = ttl or 900
    try:
        return client.generate_presigned_url(
            ClientMethod="get_object",
             Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,  # 必须
                "ACL": "public-read",         # R2 会忽略 ACL，但保留无害
            },
            ExpiresIn=3600,
            HttpMethod="PUT",
          
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Failed to generate download URL") from exc


def get_bytes(key: str) -> bytes:
    client = _client()
    bucket = _env("S3_BUCKET")
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


def put_bytes(key: str, data: bytes, *, content_type: str = "image/webp") -> Optional[str]:
    client = _client()
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        return None
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            ACL="public-read",
        )
    except (ClientError, BotoCoreError):
        return None
    public = public_url_for(key)
    if public:
        return public
    endpoint = _env("S3_ENDPOINT")
    if not endpoint:
        return None
    return f"{endpoint.rstrip('/')}/{bucket}/{quote(key)}"


__all__ = [
    "get_client",
    "make_key",
    "public_url_for",
    "presigned_put_url",
    "presigned_get_url",
    "get_bytes",
    "put_bytes",
]
