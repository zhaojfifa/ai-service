#!/usr/bin/env python3
"""
check_docs_router.py — lightweight documentation-governance guard.

Pilot for task POSTER2-DOCS-INDEX-ROUTER-SKILL-PILOT-V1 (adapted from the docs-index-router skill template to
this repository's real layout). Docs-governance only; touches no product code.

Policy (see docs/DOCS_INDEX_AND_ROUTER.md §15):
  ERROR (exit 1):
    - docs/DOCS_INDEX_AND_ROUTER.md missing
    - PROJECT_STATUS.md missing OR does not reference the router
    - a NEW/CHANGED markdown OUTSIDE docs/poster2/ and outside the governance allowlist that is either
      in a disallowed route or missing the required metadata block
  WARN (exit 0):
    - legacy root-level one-off markdown (archive-later, not moved)
    - current-phase CUISTANCE docs missing the metadata block
    - duplicate alignment-style docs
  EXEMPT (not error-checked):
    - the broad docs/poster2/** corpus (governed by docs/poster2/README.md)
    - docs/ published-frontend-mirror artifacts (*.html/*.js/*.css)

"new/changed" is detected via git (diff vs main + untracked). If git is unavailable, everything is treated as
legacy (warn-only) so the script still runs and reports honestly.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ROUTER = "docs/DOCS_INDEX_AND_ROUTER.md"
PROJECT_STATUS = "PROJECT_STATUS.md"
POSTER2_INDEX = "docs/poster2/README.md"

# root-level markdown allowed as governance/index
ALLOWED_ROOT_MD = {
    "AGENTS.md", "CLAUDE.md", "README.md", "PROJECT_STATUS.md", "PROJECT_INDEX.md",
}
# legacy root one-offs: allowed but archive-later (warn, never error)
LEGACY_ROOT_MD = {
    "APPLY_EDIT_ENABLE_PATCH.md", "DEPLOYMENT_CONFIG_TRUTH.md", "KITPOSTER_EDIT_QUALITY_AUDIT.md",
    "POST_RECOVERY_AUDIT.md", "POSTER_EDIT_PATH_REVIEW.md", "SAFE_PATCH_PLAN.md",
    "task4_handoff.md", "VERIFICATION_CHECKLIST.md",
}

# current-phase CUISTANCE docs — advisory (warn) metadata check
CUISTANCE_ACTIVE_GLOB = "docs/poster2/cuistance_commercial_trial_*.md"

METADATA_FIELDS = [
    "Purpose:", "Status:", "Scope:", "Source dependencies:", "Owner gate:", "Next action:",
]

# routes where documentation may live (markdown)
ALLOWED_DOC_PREFIXES = ("docs/",)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.oks: list[str] = []

    def error(self, m: str) -> None:
        self.errors.append(m)

    def warn(self, m: str) -> None:
        self.warnings.append(m)

    def ok(self, m: str) -> None:
        self.oks.append(m)


def _git(*args: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=False, timeout=20
        )
        if out.returncode != 0:
            return []
        return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    except Exception:
        return []


def new_or_changed_markdown() -> set[str]:
    """Markdown changed vs main + untracked. Empty set if git unavailable."""
    changed = set()
    base = _git("merge-base", "HEAD", "main")
    rng = f"{base[0]}...HEAD" if base else "HEAD"
    for ln in _git("diff", "--name-only", rng):
        if ln.endswith(".md"):
            changed.add(ln)
    for ln in _git("ls-files", "--others", "--exclude-standard"):
        if ln.endswith(".md"):
            changed.add(ln)
    return changed


def has_metadata(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:1500]
    except Exception:
        return False
    return all(f in head for f in METADATA_FIELDS)


def is_mirror_artifact(rel: str) -> bool:
    # docs/ doubles as the published frontend mirror; non-md files there are not documentation
    return rel.startswith("docs/") and not rel.endswith(".md")


def check_router(rep: Report) -> None:
    if (REPO / ROUTER).is_file():
        rep.ok(f"router present: {ROUTER}")
    else:
        rep.error(f"router missing: {ROUTER}")


def check_project_status(rep: Report) -> None:
    p = REPO / PROJECT_STATUS
    if not p.is_file():
        rep.error(f"{PROJECT_STATUS} missing (must reference {ROUTER})")
        return
    text = p.read_text(encoding="utf-8", errors="ignore")
    if ROUTER in text:
        rep.ok(f"{PROJECT_STATUS} references {ROUTER}")
    else:
        rep.error(f"{PROJECT_STATUS} does not reference {ROUTER}")
    if POSTER2_INDEX in text:
        rep.ok(f"{PROJECT_STATUS} references POSTER2 index {POSTER2_INDEX}")
    else:
        rep.warn(f"{PROJECT_STATUS} should reference POSTER2 index {POSTER2_INDEX}")


def check_root_markdown(rep: Report, changed: set[str]) -> None:
    for p in sorted(REPO.glob("*.md")):
        rel = p.name
        if rel in ALLOWED_ROOT_MD:
            continue
        if rel in LEGACY_ROOT_MD:
            rep.warn(f"legacy root doc (archive-later, not moved): {rel}")
            continue
        # unknown root markdown
        if rel in changed:
            rep.error(f"new/changed root markdown not in allowlist: {rel} (move under docs/ or add to allowlist)")
        else:
            rep.warn(f"unrecognized root markdown (legacy): {rel}")


def _is_governance_home(rel: str) -> bool:
    """Governance home = top-level docs/<name>.md (where this router lives). New docs here are ERROR-checked
    for metadata. Deeper docs/ subdirs (poster2, harness-x, architecture, execution, prompts, templates, ...)
    are legacy/auxiliary corpora governed elsewhere -> advisory only."""
    return rel.startswith("docs/") and rel.endswith(".md") and rel.count("/") == 1


def check_metadata(rep: Report, changed: set[str]) -> None:
    # ERROR: new/changed markdown in the GOVERNANCE HOME (top-level docs/*.md) must carry the metadata block.
    # Deeper docs/ subdirs and the poster2 corpus are legacy/auxiliary -> advisory (warn), never error
    # (avoids penalising historical docs that predate this rule; see DOCS_INDEX_AND_ROUTER.md §12/§15).
    for rel in sorted(changed):
        if is_mirror_artifact(rel) or not rel.endswith(".md"):
            continue
        if Path(rel).name in ALLOWED_ROOT_MD:
            continue
        fp = REPO / rel
        if not fp.is_file():
            continue
        if _is_governance_home(rel):
            if has_metadata(fp):
                rep.ok(f"metadata present: {rel}")
            else:
                rep.error(f"new governance doc missing metadata block ({', '.join(METADATA_FIELDS)}): {rel}")
        elif rel.startswith("docs/poster2/"):
            continue  # poster2 corpus exempt (advisory handled below)
        elif rel.startswith(ALLOWED_DOC_PREFIXES):
            # auxiliary/legacy docs subdir (harness-x, architecture, execution, ...) -> advisory only
            if not has_metadata(fp):
                rep.warn(f"auxiliary/legacy doc missing metadata block (advisory): {rel}")
        else:
            rep.warn(f"markdown outside docs/ route (legacy/advisory): {rel}")
    # ADVISORY: current-phase CUISTANCE docs missing metadata -> warn only
    for p in sorted(REPO.glob(CUISTANCE_ACTIVE_GLOB)):
        if not has_metadata(p):
            rep.warn(f"CUISTANCE active doc missing metadata block (advisory): {p.relative_to(REPO)}")


def check_duplicate_alignment(rep: Report) -> None:
    aligns = sorted(REPO.glob("docs/poster2/*alignment*plan*.md"))
    if len(aligns) > 1:
        names = ", ".join(p.name for p in aligns)
        rep.warn(f"multiple alignment-plan docs (consider consolidating): {names}")
    else:
        rep.ok("no duplicate alignment-plan docs")


def main() -> int:
    ap = argparse.ArgumentParser(description="Documentation router governance check.")
    ap.add_argument("--all", action="store_true", help="run all checks")
    args = ap.parse_args()
    if not args.all:
        ap.print_help()
        return 0

    rep = Report()
    changed = new_or_changed_markdown()
    git_mode = "git" if changed or _git("rev-parse", "HEAD") else "no-git(legacy-only)"

    check_router(rep)
    check_project_status(rep)
    check_root_markdown(rep, changed)
    check_metadata(rep, changed)
    check_duplicate_alignment(rep)

    print(f"docs-router check  [detection mode: {git_mode}]  changed-md={len(changed)}")
    print(f"  OK={len(rep.oks)}  WARN={len(rep.warnings)}  ERROR={len(rep.errors)}")
    for m in rep.oks:
        print(f"  [ok]    {m}")
    for m in rep.warnings:
        print(f"  [warn]  {m}")
    for m in rep.errors:
        print(f"  [ERROR] {m}")
    if rep.errors:
        print("RESULT: FAIL (errors present)")
        return 1
    print("RESULT: PASS (warnings are legacy/advisory, non-blocking)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
