from __future__ import annotations

import json
from pathlib import Path

from head_controller.llm_call_guard import run_guarded_llm_analysis
from replay_lab.paths import REPLAY_STORE_DIR


def run_head_controller_llm_guard_v5561(reports_dir: str | Path = "docs/reports", llm_provider: str = "auto", key_file: str | None = None, smoke: bool = False) -> dict:
    result = run_guarded_llm_analysis(str(reports_dir), llm_provider, key_file, smoke)
    out = REPLAY_STORE_DIR / "reports" / "head_controller_llm_guard_v5561"
    out.mkdir(parents=True, exist_ok=True)
    (out / ("llm_smoke.json" if smoke else "llm_guard.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
