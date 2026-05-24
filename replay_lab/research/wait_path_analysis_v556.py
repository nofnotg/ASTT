from __future__ import annotations

import json
from pathlib import Path

from execution.wait_path_analyzer import analyze_wait_paths
from replay_lab.paths import REPLAY_STORE_DIR


def run_wait_path_analysis_v556(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555") -> dict:
    result = analyze_wait_paths(sessions_dir)
    out = REPLAY_STORE_DIR / "reports" / "entry_discovery_v556"
    out.mkdir(parents=True, exist_ok=True)
    (out / "wait_path_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
