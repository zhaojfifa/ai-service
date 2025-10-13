#!/usr/bin/env bash
set -euo pipefail

REMOTE_ORIGIN="origin"
REMOTE_CODEX="codex"
BRANCH="main"
SOURCE_REMOTE="$REMOTE_ORIGIN"
PUSH_CHANGES=false

function usage() {
  cat <<USAGE
Usage: $0 [--source <origin|codex>] [--push]

Synchronise the local $BRANCH branch with the selected remote and ensure the
other remote is aligned. By default the GitHub remote (origin) is treated as
canonical. Use --source codex to treat the Codex remote as the source of truth.

  --source <remote>  Choose which remote provides the canonical $BRANCH commit.
  --push             After updating local refs, push the canonical commit to both
                     remotes when one is behind. Without this flag the script
                     only prints the git push command you should run.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      shift || { echo "Missing value for --source" >&2; exit 1; }
      case "$1" in
        origin|codex)
          SOURCE_REMOTE="$1"
          ;;
        *)
          echo "Unknown --source value: $1" >&2
          usage
          exit 1
          ;;
      esac
      ;;
    --push)
      PUSH_CHANGES=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

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
      echo "Configure HTTPS_PROXY/ALL_PROXY or switch to an SSH remote before retrying." >&2
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
  echo "Add the missing remote(s) before running this script." >&2
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

CANONICAL_REMOTE="$REMOTE_ORIGIN"
SECONDARY_REMOTE="$REMOTE_CODEX"
if [[ "$SOURCE_REMOTE" == "$REMOTE_CODEX" ]]; then
  CANONICAL_REMOTE="$REMOTE_CODEX"
  SECONDARY_REMOTE="$REMOTE_ORIGIN"
fi

canonical_ref="$(git rev-parse "$CANONICAL_REMOTE/$BRANCH")"
secondary_ref="$(git rev-parse "$SECONDARY_REMOTE/$BRANCH")"

echo "Canonical remote: $CANONICAL_REMOTE/$BRANCH -> $canonical_ref"

if git rev-parse --verify --quiet "refs/heads/$BRANCH" >/dev/null 2>&1; then
  git update-ref "refs/heads/$BRANCH" "$canonical_ref"
  echo "Updated local $BRANCH to $canonical_ref"
else
  git branch "$BRANCH" "$canonical_ref" >/dev/null 2>&1
  echo "Created local $BRANCH tracking $CANONICAL_REMOTE/$BRANCH"
fi

if git rev-parse --verify --quiet "refs/remotes/$CANONICAL_REMOTE/$BRANCH" >/dev/null 2>&1; then
  git update-ref "refs/remotes/$CANONICAL_REMOTE/$BRANCH" "$canonical_ref"
fi

git branch --set-upstream-to="$CANONICAL_REMOTE/$BRANCH" "$BRANCH" >/dev/null 2>&1 || true

if [[ "$canonical_ref" == "$secondary_ref" ]]; then
  echo "Remotes already share the same commit."
  if [[ "$PUSH_CHANGES" == true ]]; then
    echo "Pushing canonical commit to both remotes..."
    git push "$CANONICAL_REMOTE" "$BRANCH:$BRANCH"
    git push "$SECONDARY_REMOTE" "$BRANCH:$BRANCH"
  fi
  exit 0
fi

base="$(git merge-base "$canonical_ref" "$secondary_ref" || true)"
if [[ -z "$base" ]]; then
  echo "The remotes have no common merge-base for $BRANCH. Resolve manually." >&2
  exit 2
fi

if [[ "$base" == "$secondary_ref" ]]; then
  echo "$SECONDARY_REMOTE/$BRANCH is behind $CANONICAL_REMOTE/$BRANCH."
  if [[ "$PUSH_CHANGES" == true ]]; then
    echo "Fast-forwarding $SECONDARY_REMOTE/$BRANCH to $canonical_ref"
    git push "$SECONDARY_REMOTE" "$BRANCH:$BRANCH"
  else
    echo "Run: git push $SECONDARY_REMOTE $BRANCH:$BRANCH" >&2
  fi
  exit 0
fi

if [[ "$base" == "$canonical_ref" ]]; then
  echo "$CANONICAL_REMOTE/$BRANCH is behind $SECONDARY_REMOTE/$BRANCH." >&2
  echo "Consider re-running with --source $SECONDARY_REMOTE or resolving manually." >&2
  if [[ "$PUSH_CHANGES" == true ]]; then
    echo "Attempting to push $SECONDARY_REMOTE/$BRANCH back to $CANONICAL_REMOTE" >&2
    if ! git push "$CANONICAL_REMOTE" "$BRANCH:$BRANCH"; then
      echo "Push to $CANONICAL_REMOTE failed. Resolve conflicts and retry." >&2
      exit 3
    fi
  else
    echo "Run: git push $CANONICAL_REMOTE $BRANCH:$BRANCH" >&2
  fi
  exit 0
fi

echo "Remotes have diverged (both contain unique commits). Resolve manually." >&2
exit 2

