import os, requests, base64, mimetypes
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional

GLIB_URL = os.getenv("GLIB_URL", "").strip()
GLIB_KEY = os.getenv("GLIB_KEY", "").strip()
ATTACH_IMAGE = os.getenv("ATTACH_IMAGE", "false").lower() == "true"
CORS_ALLOW = [o.strip() for o in os.getenv(
    "CORS_ALLOW_ORIGINS",
    "https://<your-frontend-host>,http://localhost:5173,http://localhost:3000"
).split(",") if o.strip()]

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")

app = FastAPI(title="ai-service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateReq(BaseModel):
    prompt: str
    email: Optional[EmailStr] = None
    subject: Optional[str] = "海报已生成"
    size: Optional[str] = "960x1200"   # 视你的 Glibatree API 而定
    metadata: Optional[dict] = None

class GenerateResp(BaseModel):
    ok: bool
    image_url: Optional[str] = None
    raw: Optional[dict] = None
    mailed: bool = False
    message: Optional[str] = None

@app.get("/")
def root():
    return {"ok": True, "service": "ai-service", "version": "0.1.0"}

def call_glibatree(prompt: str, size: str) -> dict:
    if not (GLIB_URL and GLIB_KEY):
        raise HTTPException(500, "Server not configured for Glibatree (GLIB_URL/GLIB_KEY missing)")
    headers = {
        "Authorization": f"Bearer {GLIB_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt, "size": size}
    r = requests.post(GLIB_URL, json=payload, headers=headers, timeout=60)
    try:
        data = r.json()
    except Exception:
        raise HTTPException(r.status_code, f"Glibatree non-JSON response: {r.text[:200]}")
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Glibatree error: {data}")
    return data

def extract_image_url(data: dict) -> Optional[str]:
    # 兼容多种返回格式
    return (
        data.get("image_url")
        or data.get("url")
        or (data.get("data") or [{}])[0].get("url")
    )

def send_mail_smtp(to_email: str, subject: str, html: str,
                   attach_bytes: bytes | None = None,
                   attach_name: str | None = None):
    import smtplib
    from email.message import EmailMessage

    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and FROM_EMAIL):
        raise RuntimeError("SMTP not configured (SMTP_HOST/USER/PASS/FROM_EMAIL)")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("Your client doesn't support HTML.")
    msg.add_alternative(html, subtype="html")

    if attach_bytes and attach_name:
        mime, _ = mimetypes.guess_type(attach_name)
        maintype, subtype = (mime or "application/octet-stream").split("/", 1)
        msg.add_attachment(attach_bytes, maintype=maintype, subtype=subtype, filename=attach_name)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

@app.post("/generate", response_model=GenerateResp)
def generate(req: GenerateReq):
    data = call_glibatree(req.prompt, req.size or "960x1200")
    image_url = extract_image_url(data)

    mailed = False
    if req.email:
        # 默认发链接；如果 ATTACH_IMAGE=true 则尝试把图片作为附件发送
        html = f"""
        <p>海报已生成：</p>
        <p><a href="{image_url}" target="_blank">{image_url}</a></p>
        <p>提示词（节选）：</p>
        <pre style="white-space:pre-wrap">{req.prompt[:2000]}</pre>
        """
        attach_bytes = None
        attach_name = None
        if ATTACH_IMAGE and image_url:
            try:
                ir = requests.get(image_url, timeout=60)
                ir.raise_for_status()
                attach_bytes = ir.content
                # 简单推断文件名
                attach_name = "poster.jpg" if "image/" in ir.headers.get("Content-Type","") else "poster.bin"
            except Exception:
                pass
        try:
            send_mail_smtp(req.email, req.subject or "海报已生成", html, attach_bytes, attach_name)
            mailed = True
        except Exception as e:
            # 邮件失败不要阻断主流程
            return GenerateResp(ok=True, image_url=image_url, raw=data, mailed=False, message=f"mail failed: {e}")

    return GenerateResp(ok=True, image_url=image_url, raw=data, mailed=mailed)
