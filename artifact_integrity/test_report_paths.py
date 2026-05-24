from __future__ import annotations

from pathlib import Path


def test_report_dirs(tmp_path: str | Path) -> tuple[Path, Path]:
    base = Path(tmp_path)
    docs = base / "docs_reports"
    replay = base / "replay_reports"
    docs.mkdir(parents=True, exist_ok=True)
    replay.mkdir(parents=True, exist_ok=True)
    return docs, replay
