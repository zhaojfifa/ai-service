#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="${1:-assets/fonts}"
mkdir -p "$DEST_DIR"

# Download from Google Fonts / Noto (ttf). You can change URLs if you prefer a pinned release.
# Note: Keep filenames aligned with backend loader expectations.
BASE_RAW="https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/TTF/SimplifiedChinese"

curl -L --fail -o "$DEST_DIR/NotoSansSC-Regular.ttf"   "$BASE_RAW/NotoSansSC-Regular.ttf"
curl -L --fail -o "$DEST_DIR/NotoSansSC-SemiBold.ttf" "$BASE_RAW/NotoSansSC-SemiBold.ttf"

ls -lh "$DEST_DIR"
