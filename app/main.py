"""
FastAPI 入口（安全版）：
- 提供 /healthz
- 中间件“可选导入”，失败不阻塞启动
- 启动与导入阶段打印明确日志，避免 Render 出现 “No open ports detected”
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Service", version="1.0.0")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # 可选中间件：仅当模块与类均存在时启用；支持通过环境变量禁用
    if os.getenv("DISABLE_GUARD", "").lower() not in {"1", "true", "yes"}:
        try:
            mod = importlib.import_module("app.middlewares.huge_or_b64_guard")
            Guard = getattr(mod, "RejectHugeOrBase64", None)
            if Guard:
                app.add_middleware(Guard, max_bytes=4 * 1024 * 1024, check_base64=True)
                print("[guard] enabled", flush=True)
            else:
                print("[guard] not installed (class missing)", flush=True)
        except Exception:
            print("[guard] disabled by import error", flush=True)
            traceback.print_exc()
    else:
        print("[guard] disabled by env", flush=True)

    print("[boot] app object created", flush=True)
    return app


try:
    app = create_app()
    print("[boot] module import completed, app ready", flush=True)
except Exception:
    print("[boot] FATAL during module import:", file=sys.stderr, flush=True)
    traceback.print_exc()
    # 兜底：始终抛出，让平台把栈打印完整
    raise
