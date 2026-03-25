#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PAIRS=(
  "frontend/index.html:docs/index.html"
  "frontend/stage2.html:docs/stage2.html"
  "frontend/stage3.html:docs/stage3.html"
  "frontend/app.js:docs/app.js"
  "frontend/styles.css:docs/styles.css"
)

stale=0

for pair in "${PAIRS[@]}"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  if ! cmp -s "$ROOT_DIR/$src" "$ROOT_DIR/$dst"; then
    echo "stale publish mirror: $dst does not match $src" >&2
    stale=1
  fi
done

if [[ "$stale" -ne 0 ]]; then
  echo "frontend/docs publish mirror is stale" >&2
  echo "Run: scripts/sync_frontend_to_docs.sh" >&2
  exit 1
fi

echo "frontend/docs publish mirror is up to date"
