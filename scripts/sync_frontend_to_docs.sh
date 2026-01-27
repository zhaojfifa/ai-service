#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT_DIR}/frontend"
DST="${ROOT_DIR}/docs"

if [[ ! -d "${SRC}" ]]; then
  echo "[sync_frontend_to_docs] missing frontend/ at: ${SRC}" >&2
  exit 1
fi

mkdir -p "${DST}"

# preserve CNAME if exists (GitHub Pages custom domain)
CNAME_BAK=""
if [[ -f "${DST}/CNAME" ]]; then
  CNAME_BAK="$(cat "${DST}/CNAME" || true)"
fi

# hard mirror
rm -rf "${DST:?}/"*
cp -R "${SRC}/." "${DST}/"

# restore CNAME
if [[ -n "${CNAME_BAK}" ]]; then
  printf "%s\n" "${CNAME_BAK}" > "${DST}/CNAME"
fi

# touch for cache-busting / provenance
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DST}/.pages-touch"

echo "[sync_frontend_to_docs] synced frontend -> docs OK"