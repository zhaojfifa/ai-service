from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "scripts" / "sync_frontend_to_docs.sh"
CHECK_SCRIPT = ROOT / "scripts" / "check_frontend_docs_sync.sh"


def _write_asset_tree(base: Path, *, stage2: str, app: str, styles: str) -> None:
    frontend = base / "frontend"
    docs = base / "docs"
    frontend.mkdir()
    docs.mkdir()
    (frontend / "stage2.html").write_text(stage2, encoding="utf-8")
    (frontend / "app.js").write_text(app, encoding="utf-8")
    (frontend / "styles.css").write_text(styles, encoding="utf-8")
    (docs / "stage2.html").write_text(stage2, encoding="utf-8")
    (docs / "app.js").write_text(app, encoding="utf-8")
    (docs / "styles.css").write_text(styles, encoding="utf-8")


def _env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FRONTEND_DIR"] = str(tmp_path / "frontend")
    env["DOCS_DIR"] = str(tmp_path / "docs")
    return env


def test_check_frontend_docs_sync_detects_stale_publish_files(tmp_path: Path):
    _write_asset_tree(tmp_path, stage2="new stage2", app="console.log('new')", styles="body{color:red;}")
    (tmp_path / "docs" / "app.js").write_text("console.log('old')", encoding="utf-8")

    proc = subprocess.run(
        ["bash", str(CHECK_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "stale publish mirror: app.js" in proc.stderr


def test_sync_frontend_to_docs_restores_publish_mirror(tmp_path: Path):
    _write_asset_tree(tmp_path, stage2="new stage2", app="console.log('new')", styles="body{color:red;}")
    (tmp_path / "docs" / "stage2.html").write_text("old stage2", encoding="utf-8")

    subprocess.run(
        ["bash", str(SYNC_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["bash", str(CHECK_SCRIPT)],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        check=True,
    )

    assert (tmp_path / "docs" / "stage2.html").read_text(encoding="utf-8") == "new stage2"
