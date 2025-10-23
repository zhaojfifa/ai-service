from __future__ import annotations

import os
from datetime import datetime
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.s3_client import make_key, presigned_put_url, public_url_for

router = APIRouter(prefix="/api/r2", tags=["r2"])


class PresignPutRequest(BaseModel):
    filename: str = Field(..., description="Original filename supplied by the browser")
    content_type: str = Field(..., description="Detected MIME type of the upload")
    folder: str | None = Field("assets/user", description="Target logical folder for the asset")
    size: int | None = Field(None, ge=0, description="Optional size hint for validation")


class PresignPutResponse(BaseModel):
    key: str
    upload_url: str
    public_url: str


UPLOAD_MAX_BYTES = max(int(os.getenv("UPLOAD_MAX_BYTES", "20000000") or 0), 0)
UPLOAD_ALLOWED_MIME = {
    item.strip()
    for item in os.getenv("UPLOAD_ALLOWED_MIME", "image/png,image/jpeg,image/webp").split(",")
    if item.strip()
}


def _build_key(folder: str | None, filename: str) -> str:
    folder = (folder or "assets/user").strip()
    if folder:
        folder = folder.strip("/")
    else:
        folder = "assets/user"
    # incorporate a timestamp token to make browser uploads easier to audit
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(4)
    name = filename.rsplit("/", 1)[-1].replace(" ", "_")
    return make_key(f"{folder}/{ts}-{suffix}", name)


def _make_presigned_put_url(key: str, content_type: str) -> str:
    return presigned_put_url(key, content_type)


@router.post("/presign-put", response_model=PresignPutResponse)
def presign_put(req: PresignPutRequest) -> PresignPutResponse:
    if UPLOAD_ALLOWED_MIME and req.content_type not in UPLOAD_ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"content_type not allowed: {req.content_type}")
    if UPLOAD_MAX_BYTES and req.size and req.size > UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds permitted size")

    try:
        key = _build_key(req.folder, req.filename)
        upload_url = _make_presigned_put_url(key, req.content_type)
        public_url = public_url_for(key)
        if not public_url:
            raise RuntimeError("S3_PUBLIC_BASE is not configured")
        return PresignPutResponse(key=key, upload_url=upload_url, public_url=public_url)
    except Exception as exc:  # pragma: no cover - transport/R2 errors
        raise HTTPException(status_code=500, detail=f"presign failed: {exc}") from exc
