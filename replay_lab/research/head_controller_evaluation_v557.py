from __future__ import annotations

import json
from pathlib import Path

from head_controller.head_controller_evaluation_loop import run_head_controller_evaluation_loop
from replay_lab.paths import REPLAY_STORE_DIR


def run_head_controller_evaluation_v557(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict:
    result = run_head_controller_evaluation_loop(reports_dir, llm_provider)
    out = REPLAY_STORE_DIR / "reports" / "head_controller_evaluation_v557"
    out.mkdir(parents=True, exist_ok=True)
    (out / "head_controller_evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
