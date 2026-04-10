#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${FRONTEND_DIR:-$ROOT_DIR/frontend}"
DOCS_DIR="${DOCS_DIR:-$ROOT_DIR/docs}"

FILES=(
  "index.html"
  "stage2.html"
  "app.js"
  "styles.css"
  "stage2_request_helpers.js"
)

for rel in "${FILES[@]}"; do
  src="$FRONTEND_DIR/$rel"
  dst="$DOCS_DIR/$rel"
  if [[ ! -f "$src" ]]; then
    echo "missing frontend source: $src" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "synced $rel"
done

echo "frontend -> docs publish assets are in sync"
