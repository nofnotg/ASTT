from __future__ import annotations

import json
from pathlib import Path

from head_controller.head_controller_analyzer import analyze_head_controller_context
from head_controller.head_controller_context_builder import build_head_controller_context
from head_controller.llm_config import build_head_controller_llm_config
from replay_lab.paths import REPLAY_STORE_DIR


def run_head_controller_draft_v556(reports_dir: str | Path = "docs/reports", llm_provider: str = "off", key_file: str | None = None) -> dict:
    llm_config = build_head_controller_llm_config(llm_provider, key_file)
    context = build_head_controller_context(reports_dir, llm_config)
    result = analyze_head_controller_context(context)
    out = REPLAY_STORE_DIR / "reports" / "head_controller_v556"
    out.mkdir(parents=True, exist_ok=True)
    (out / "head_controller_draft.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
