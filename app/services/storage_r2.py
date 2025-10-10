from __future__ import annotations

import os
from typing import Optional

import boto3


def _client():
    endpoint = os.getenv("S3_ENDPOINT")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    region = os.getenv("S3_REGION", "auto")
    if not (endpoint and access_key and secret_key):
        return None
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def put_bytes(key: str, data: bytes, content_type: str = "image/webp") -> Optional[str]:
    """Upload bytes to R2. Return a public URL when configured."""

    client = _client()
    if not client:
        return None

    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        return None

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        ACL="public-read",
    )

    public_base = os.getenv("S3_PUBLIC_BASE")
    if public_base:
        return f"{public_base.rstrip('/')}/{key}"

    endpoint = os.getenv("S3_ENDPOINT", "").rstrip("/")
    return f"{endpoint}/{bucket}/{key}"
