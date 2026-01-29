#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="${1:-assets/fonts}"
mkdir -p "$DEST_DIR"

# Download from Google Fonts / Noto (variable ttf).
# Note: Keep filenames aligned with backend loader expectations.
BASE_RAW="https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/Variable/TTF"
SRC_FILE="NotoSansCJKsc-VF.ttf"

if [[ ! -f "$DEST_DIR/NotoSansSC-Regular.ttf" ]]; then
  curl -L --fail -o "$DEST_DIR/NotoSansSC-Regular.ttf" "$BASE_RAW/$SRC_FILE"
fi

if [[ ! -f "$DEST_DIR/NotoSansSC-SemiBold.ttf" ]]; then
  curl -L --fail -o "$DEST_DIR/NotoSansSC-SemiBold.ttf" "$BASE_RAW/$SRC_FILE"
fi

ls -lh "$DEST_DIR"
