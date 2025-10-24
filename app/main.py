"""FastAPI entrypoint with health probe and optional request-guard middleware."""
from __future__ import annotations

import importlib
import os

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Marketing Poster API", version="1.0.0")

    @app.get("/healthz")
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    disable_guard = os.getenv("DISABLE_GUARD", "false").lower() in {"1", "true", "yes"}

    Guard = None
    try:
        mod = importlib.import_module("app.middlewares.huge_or_b64_guard")
        Guard = getattr(mod, "RejectHugeOrBase64", None)
        print("[guard] import ok:", Guard, flush=True)
    except Exception as exc:  # pragma: no cover - defensive logging
        print("[guard] import disabled:", repr(exc), flush=True)

    try:
        if not disable_guard and Guard:
            app.add_middleware(Guard, max_bytes=4 * 1024 * 1024, check_base64=True)
            print("[guard] middleware enabled", flush=True)
        else:
            print("[guard] middleware NOT installed (disabled or missing)", flush=True)
    except Exception as exc:  # pragma: no cover - defensive logging
        print("[guard] add_middleware failed:", repr(exc), flush=True)

    # TODO: include routers here once modules are ready.

    return app


app = create_app()
