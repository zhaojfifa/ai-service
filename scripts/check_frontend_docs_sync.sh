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
)

stale=0
for rel in "${FILES[@]}"; do
  src="$FRONTEND_DIR/$rel"
  dst="$DOCS_DIR/$rel"
  if [[ ! -f "$src" ]]; then
    echo "missing frontend source: $src" >&2
    exit 1
  fi
  if [[ ! -f "$dst" ]]; then
    echo "missing docs publish file: $dst" >&2
    stale=1
    continue
  fi
  if ! cmp -s "$src" "$dst"; then
    echo "stale publish mirror: $rel" >&2
    stale=1
  fi
done

if [[ "$stale" -ne 0 ]]; then
  echo "frontend/docs publish assets are out of sync" >&2
  exit 1
fi

echo "frontend/docs publish assets are in sync"
