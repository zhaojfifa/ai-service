"""
FastAPI 安全入口：
 - /healthz 常驻
 - 中间件可选启用（导入失败不阻塞）
 - 打印 COMMIT_SHA 与文件版本戳，便于确认线上实际生效文件
"""
from __future__ import annotations

import importlib
import os
import time
import traceback
from fastapi import FastAPI

BOOT_TS = str(int(time.time()))
COMMIT = os.getenv("COMMIT_SHA", "local")

def create_app() -> FastAPI:
    app = FastAPI(title="AI Service", version=f"boot:{BOOT_TS}, commit:{COMMIT}")

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "boot": BOOT_TS, "commit": COMMIT}

    # 可选中间件：仅当模块和类均存在时启用；可用 env 临时禁用
    if os.getenv("DISABLE_GUARD", "").lower() not in {"1", "true", "yes"}:
        try:
            mod = importlib.import_module("app.middlewares.huge_or_b64_guard")
            Guard = getattr(mod, "RejectHugeOrBase64", None)
            if Guard:
                app.add_middleware(Guard, max_bytes=4 * 1024 * 1024, check_base64=True)
                print(f"[guard] enabled (commit={COMMIT})", flush=True)
            else:
                print(f"[guard] not present (commit={COMMIT})", flush=True)
        except Exception:
            print(f"[guard] import error (commit={COMMIT})", flush=True)
            traceback.print_exc()
    else:
        print(f"[guard] disabled by env (commit={COMMIT})", flush=True)

    print(f"[boot] app created (commit={COMMIT}, ts={BOOT_TS})", flush=True)
    return app

app = create_app()
print(f"[boot] module loaded, app ready (commit={COMMIT})", flush=True)
