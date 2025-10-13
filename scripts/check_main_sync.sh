#!/usr/bin/env bash
set -euo pipefail

REMOTE_ORIGIN="origin"
REMOTE_CODEX="codex"
BRANCH="main"

function remote_exists() {
  git remote get-url "$1" >/dev/null 2>&1
}

function fetch_branch() {
  local remote="$1"
  local branch="$2"
  if ! output=$(git fetch "$remote" "$branch" 2>&1); then
    echo "Failed to fetch $remote/$branch" >&2
    if [[ "$output" == *"CONNECT tunnel failed"* ]]; then
      echo "It looks like the environment blocked outbound HTTPS traffic (CONNECT tunnel failed)." >&2
      echo "Try configuring HTTPS_PROXY/ALL_PROXY or use a GitHub token/SSH remote before retrying." >&2
    fi
    echo "$output" >&2
    exit 1
  fi
}

missing=()
if ! remote_exists "$REMOTE_ORIGIN"; then
  missing+=("$REMOTE_ORIGIN")
fi
if ! remote_exists "$REMOTE_CODEX"; then
  missing+=("$REMOTE_CODEX")
fi

if (( ${#missing[@]} > 0 )); then
  echo "Missing remote(s): ${missing[*]}" >&2
  echo "Add the missing remote(s) before running this script again." >&2
  echo "Example: git remote add origin <github-repo-url>" >&2
  echo "         git remote add codex <codex-repo-url>" >&2
  exit 1
fi

fetch_branch "$REMOTE_ORIGIN" "$BRANCH"
fetch_branch "$REMOTE_CODEX" "$BRANCH"

if ! git rev-parse --verify --quiet "$REMOTE_ORIGIN/$BRANCH"; then
  echo "Remote $REMOTE_ORIGIN does not have branch $BRANCH" >&2
  exit 1
fi
if ! git rev-parse --verify --quiet "$REMOTE_CODEX/$BRANCH"; then
  echo "Remote $REMOTE_CODEX does not have branch $BRANCH" >&2
  exit 1
fi

origin_ref="$(git rev-parse "$REMOTE_ORIGIN/$BRANCH")"
codex_ref="$(git rev-parse "$REMOTE_CODEX/$BRANCH")"

if [[ "$origin_ref" == "$codex_ref" ]]; then
  echo "Remotes are in sync: $origin_ref"
  exit 0
fi

echo "Remotes are out of sync!" >&2
echo "$REMOTE_ORIGIN/$BRANCH: $origin_ref" >&2
echo "$REMOTE_CODEX/$BRANCH: $codex_ref" >&2
echo "Update the older branch so both point to the same commit." >&2
exit 2
