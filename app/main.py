# app/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Response

# FIX: 先导入 get_settings，再调用，否则会 NameError
from app.config import get_settings  # FIX: moved up

from app.schemas import (
    GeneratePosterResponse,
    PosterInput,
    SendEmailRequest,
    SendEmailResponse,
)
from app.services.email_sender import send_email

# ---- 初始化配置 & 应用 -------------------------------------------------
settings = get_settings()           # FIX: moved below import
app = FastAPI(title="Marketing Poster API", version="1.0.0")  # FIX: app 在所有装饰器之前

# === 根路径：避免 Render 探活 404 ===
@app.get("/", include_in_schema=False)
def index():
    # 访问根路径时跳到 API 文档
    return RedirectResponse(url="/docs", status_code=307)

@app.head("/", include_in_schema=False)
def index_head():
    # Render 探活会发 HEAD /，这里返回 204 即可
    return Response(status_code=204)
# === End ===

# ---- 方案 2：OpenAI 生成海报 ------------------------------------------
try:
    # 新版 SDK：pip install openai>=1.40.0
    from openai import OpenAI
except Exception:
    OpenAI = None  # 启动不报错；真正调用时再抛出

# 允许跨域
allow_origins = settings.allowed_origins
allow_credentials = False if allow_origins == ["*"] else True

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

def _build_openai_prompt(poster: PosterInput) -> str:
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
    使用 OpenAI 生成 base64 PNG 字符串。
    依赖环境变量 OPENAI_API_KEY（在 settings.OPENAI_API_KEY）。
    """
    if not OpenAI:
        raise RuntimeError("OpenAI SDK 未安装，请在 requirements.txt 加入 openai>=1.40.0")
    if not getattr(settings, "OPENAI_API_KEY", None):
        raise RuntimeError("未配置 OPENAI_API_KEY，无法调用 OpenAI 生成海报")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = _build_openai_prompt(poster)
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json",
    )
    return result.data[0].b64_json

@app.post("/api/generate-poster", response_model=GeneratePosterResponse)
def generate_poster_asset(payload: PosterInput) -> GeneratePosterResponse:
    try:
        poster_image_b64 = _openai_generate_image(payload)
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
        return GeneratePosterResponse(
            email_body=email_body,
            poster_image={"content": poster_image_b64, "format": "png"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/send-email", response_model=SendEmailResponse)
def send_marketing_email(payload: SendEmailRequest) -> SendEmailResponse:
    try:
        return send_email(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

__all__ = ["app"]
