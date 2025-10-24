import os
import importlib
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Marketing Poster API", version="1.0.0")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # ---- 可选安装：拒绝大包/含 base64 的请求 ----
    DISABLE_GUARD = os.getenv("DISABLE_GUARD", "false").lower() in ("1", "true", "yes")

    Guard = None
    try:
        # 如你使用其他文件名，请把路径改为真实路径
        mod = importlib.import_module("app.middlewares.huge_or_b64_guard")
        Guard = getattr(mod, "RejectHugeOrBase64", None)
        print("[guard] import ok:", Guard)
    except Exception as e:
        print("[guard] import disabled:", repr(e))

    try:
        if not DISABLE_GUARD and Guard:
            # 可改成从 settings 读取
            app.add_middleware(Guard, max_bytes=4 * 1024 * 1024, check_base64=True)
            print("[guard] middleware enabled")
        else:
            print("[guard] middleware NOT installed (disabled or missing)")
    except Exception as e:
        print("[guard] add_middleware failed:", repr(e))

    # TODO: include your routers
    # from app.api import router as api_router
    # app.include_router(api_router)

    return app

# Uvicorn 入口
app = create_app()
