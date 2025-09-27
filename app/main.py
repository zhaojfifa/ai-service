# app/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Response
from app.config import get_settings
from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_sender import send_email
# === Add: 根路径的 GET/HEAD 响应，避免 Render 探活 404 ===


@app.get("/", include_in_schema=False)
def index():
    # 访问根路径时跳到 API 文档
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def index_head():
    # Render 探活会发 HEAD /，这里返回 204 即可
    return Response(status_code=204)
# === End Add ===

# [ADDED] —— OpenAI 客户端（方案2：用 OpenAI 生成海报替代 Glibatree）
# -----------------------------------------------------------
try:
    # 新版 SDK：pip install openai>=1.40.0
    from openai import OpenAI  # [ADDED]
except Exception as _:
    OpenAI = None  # 便于启动时不报错；若调用时仍为 None 会抛出 500

# -----------------------------------------------------------

settings = get_settings()
app = FastAPI(title="Marketing Poster API", version="1.0.0")

# 允许跨域
allow_origins = settings.allowed_origins
if allow_origins == ["*"]:
    allow_credentials = False
else:
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# [CHANGED] —— 方案2：使用 OpenAI 生成海报图像
# -----------------------------------------------------------
def _build_openai_prompt(poster: PosterInput) -> str:
    """把结构化输入转成图像生成提示词。"""
    features_text = "；".join(poster.features or [])
    series_text = poster.series or "三视图/系列款式"
    prompt = f"""
    以广告海报形式输出一张「{poster.brand_name} {poster.product_name}」的宣传图：
    - 风格现代、简洁，主色黑/红/灰银；背景浅色，留白充足；
    - 版式：顶部横条（左：品牌Logo字样“{poster.brand_name}”，右：代理名“{poster.agent_name or '官方渠道'}”）；
    - 左侧约40%放置应用场景：{poster.scene or '厨房场景'}；
    - 右侧视觉中心：45°产品渲染，保持金属/塑料质感清晰；
    - 在产品周边加 3–4 条功能点虚线标注：{features_text if features_text else '高效加热；节能节省；易清洁；小巧便携'}；
    - 中部大标题（红色粗体）：“{poster.title or '新一代厨房电器解决方案'}”；
    - 底部横向 3–4 张小图（灰度/黑白），表示三视图或系列款式：{series_text}；
    - 右下角副标题（红色粗体）：“{poster.subtitle or '智造好厨房'}”；
    输出画面像素清晰、画面规整对齐、易读且专业的广告海报。
    """
    return " ".join(line.strip() for line in prompt.splitlines() if line.strip())


def _openai_generate_image(poster: PosterInput) -> str:
    """
    调用 OpenAI 生成图片（base64）。返回 base64 PNG 字符串。
    依赖环境变量 OPENAI_API_KEY（通过 settings.OPENAI_API_KEY 获取）
    """
    if not OpenAI:
        raise RuntimeError("OpenAI SDK 未安装，请在 requirements.txt 加入 openai>=1.40.0")

    if not getattr(settings, "OPENAI_API_KEY", None):
        raise RuntimeError("未配置 OPENAI_API_KEY，无法调用 OpenAI 生成海报")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)  # [ADDED]

    prompt = _build_openai_prompt(poster)
    # 生成图像，b64_json 返回 base64 数据
    result = client.images.generate(  # [ADDED]
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json",
    )
    image_b64 = result.data[0].b64_json
    return image_b64
# -----------------------------------------------------------


@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster_asset(payload: PosterInput) -> GeneratePosterResponse:
    """
    方案2：改为调用 OpenAI 生成海报（base64）。
    """
    try:
        poster_image_b64 = _openai_generate_image(payload)  # [CHANGED]
        # 这里也可以构造一个邮件正文，用于发送
        feature_lines = "\n".join(f"• {f}" for f in (payload.features or []))
        email_body = f"""尊敬的客户，您好！

感谢关注 {payload.brand_name} 厨房解决方案。
我们最新推出的 {payload.product_name} 已经上线，随附海报供您推广使用。

功能亮点：
{feature_lines or '• 高效加热\n• 节能省电\n• 易清洁\n• 小巧便携'}

海报主题：{payload.title or "新一代厨房电器解决方案"}
副标题：{payload.subtitle or "智造好厨房"}

祝商祺！
—— {payload.brand_name} 市场团队
"""
        # 返回 base64 图像给前端预览/下载
        return GeneratePosterResponse(
            email_body=email_body,
            poster_image={"content": poster_image_b64, "format": "png"},  # [CHANGED]
        )
    except Exception as exc:  # 统一转 HTTP 友好错误
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:  # pragma: no cover - ensures HTTP friendly message
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
