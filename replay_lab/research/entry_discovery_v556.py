from __future__ import annotations

import json
from pathlib import Path

from execution.entry_discovery_simulator import simulate_entry_discovery
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.wait_path_analysis_v556 import run_wait_path_analysis_v556


def run_entry_discovery_v556(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555", profiles: str = "STRICT,BALANCED,ENTRY_DISCOVERY,DIAGNOSTIC_ONLY") -> dict:
    wait = run_wait_path_analysis_v556(sessions_dir)
    names = [item.strip() for item in str(profiles).split(",") if item.strip()]
    result = simulate_entry_discovery(wait, names)
    result["entry_discovery_enter"] = next((row["enter"] for row in result["profiles"] if row["profile"] == "ENTRY_DISCOVERY"), 0)
    out = REPLAY_STORE_DIR / "reports" / "entry_discovery_v556"
    out.mkdir(parents=True, exist_ok=True)
    (out / "entry_discovery.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
