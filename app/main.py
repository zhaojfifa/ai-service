"""
FastAPI 入口：稳健启动 + 健康探针 + 可选中间件 + 启动期详细日志。
任何导入/装配阶段抛错，都会打印完整栈，避免 Render 出现
'No open ports detected' 却看不到原因。
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Marketing Poster API", version="1.0.0")

    # 健康探针：Render/负载均衡可用它做 readiness
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # 启动钩子：确认生命周期执行到哪
    @app.on_event("startup")
    async def _startup_probe() -> None:
        print("[boot] startup hook entered", flush=True)

    # --- 可选中间件：拒绝巨大/含 base64 的请求体 ---
    # 为了避免 NameError，这里改为“可选导入 + try/except”，并支持用环境变量一键禁用
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
    raise
