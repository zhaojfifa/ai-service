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

for pair in "${PAIRS[@]}"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  cp "$ROOT_DIR/$src" "$ROOT_DIR/$dst"
  echo "synced $src -> $dst"
done

echo "frontend -> docs publish mirror sync complete"
