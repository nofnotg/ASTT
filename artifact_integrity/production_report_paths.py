from __future__ import annotations

from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR


DOCS_REPORTS_DIR = ROOT_DIR / "docs" / "reports"
REPLAY_REPORTS_DIR = REPLAY_STORE_DIR / "reports"


def production_docs_reports_dir() -> Path:
    DOCS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return DOCS_REPORTS_DIR


def production_replay_report_dir(name: str) -> Path:
    path = REPLAY_REPORTS_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path
