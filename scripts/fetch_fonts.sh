#!/usr/bin/env bash
set -euo pipefail

FONT_DIR="app/assets/fonts"

mkdir -p "${FONT_DIR}"

download_if_missing() {
  local url="$1"
  local name="$2"
  local dest="${FONT_DIR}/${name}"

  if [[ -f "${dest}" ]]; then
    echo "ok: ${name}"
    return 0
  fi

  echo "fetch: ${name}"
  curl -L --retry 3 --retry-delay 2 --retry-connrefused -o "${dest}" "${url}"
}

download_if_missing "https://github.com/google/fonts/raw/main/ofl/notosans/static/NotoSans-Regular.ttf" "NotoSans-Regular.ttf"
download_if_missing "https://github.com/google/fonts/raw/main/ofl/notosans/static/NotoSans-SemiBold.ttf" "NotoSans-SemiBold.ttf"
download_if_missing "https://github.com/google/fonts/raw/main/ofl/notosanssc/static/NotoSansSC-Regular.ttf" "NotoSansSC-Regular.ttf"
download_if_missing "https://github.com/google/fonts/raw/main/ofl/notosanssc/static/NotoSansSC-SemiBold.ttf" "NotoSansSC-SemiBold.ttf"
