#!/usr/bin/env bash
set -euo pipefail
echo "===== dump app/main.py (first 120 lines) ====="
nl -ba app/main.py | sed -n '1,120p'
echo "===== env ====="
env | sort | sed -n '1,80p'
echo "===== start uvicorn ====="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --log-level trace --lifespan on --proxy-headers
