# app/services/s3_client.py
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


def _env(name: str) -> str | None:
    v = os.getenv(name)
    if v is None:
        return None
    s = v.strip()
    return s or None


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

# 新增：规范化 public_base，自动补桶名，避免“漏桶名/双斜杠”
def _normalize_public_base() -> str | None:
    base = _normalize_public_base()
    if base:
        # key 里可能有中文/空格，按需编码；你如果全是安全字符，可不编码
        from urllib.parse import quote
        return f"{base}/{quote(key)}"
    return None
    
def public_url_for(key: str) -> str | None:
    """
    Build a public URL using S3_PUBLIC_BASE (必须配置为 R2 的 public 域，比如 r2.dev 或你的自定义域)。
    未配置则返回 None（让调用方回退 base64）。
    """
    base = _env("S3_PUBLIC_BASE")
    if base:
        return f"{base.rstrip('/')}/{key.lstrip('/')}"
    return None


def presigned_put_url(key: str, content_type: str, expires: int = 900) -> str:
    """
    生成 PUT 预签名，确保带上 ContentType，浏览器上传时对象会保存正确的 Content-Type。
    """
    client = _client()
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    try:
        return client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
                # R2 通常忽略 ACL，但保留无害；如无需要可移除
                # "ACL": "public-read",
            },
            ExpiresIn=max(int(expires), 60),
            HttpMethod="PUT",
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Failed to generate upload URL") from exc


def presigned_get_url(key: str, expires: int | None = None) -> str:
    """
    生成 GET 预签名（下载/私有读取用）。默认 TTL 来自 S3_SIGNED_GET_TTL（秒），否则 900。
    """
    client = _client()
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")

    ttl_raw = _env("S3_SIGNED_GET_TTL")
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
    bucket = _env("S3_BUCKET")
    if not (client and bucket):
        raise RuntimeError("R2 storage is not configured")
    try:
        resp = client.get_object(Bucket=bucket, Key=key)
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Failed to fetch object {key}") from exc
    body = resp.get("Body")
    if body is None:
        raise RuntimeError(f"Object {key} has no body")
    return body.read()


def put_bytes(key: str, data: bytes, *, content_type: str = "image/png") -> Optional[str]:
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
            ACL="public-read",  # R2 会忽略 ACL，但无害
        )
        # 关键：确认一下对象真的在桶里
        client.head_object(Bucket=bucket, Key=key)

    except (ClientError, BotoCoreError) as exc:
        # 打清楚一点，便于你在 Render 日志里搜
        import logging
        logging.getLogger(__name__).warning("R2 put/head failed: bucket=%s key=%s err=%s", bucket, key, exc)
        return None

    public = public_url_for(key)
    import logging
    logging.getLogger(__name__).info("R2 uploaded ok: bucket=%s key=%s url=%s", bucket, key, public)
    return public


__all__ = [
    "get_client",
    "make_key",
    "public_url_for",
    "presigned_put_url",
    "presigned_get_url",
    "get_bytes",
    "put_bytes",
]
