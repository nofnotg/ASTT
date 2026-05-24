from __future__ import annotations

import json
from pathlib import Path

from execution.hold_time_sweep_runner import run_hold_time_sweep
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.wait_path_analysis_v556 import run_wait_path_analysis_v556


def run_hold_time_sweep_v556(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555", hold_seconds: str = "60,120,180,300,600") -> dict:
    wait = run_wait_path_analysis_v556(sessions_dir)
    holds = [int(item.strip()) for item in str(hold_seconds).split(",") if item.strip()]
    result = run_hold_time_sweep(wait, holds)
    out = REPLAY_STORE_DIR / "reports" / "entry_discovery_v556"
    out.mkdir(parents=True, exist_ok=True)
    (out / "hold_time_sweep.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
