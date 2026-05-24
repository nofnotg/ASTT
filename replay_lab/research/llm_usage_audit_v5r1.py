from __future__ import annotations

import json
from pathlib import Path

from llm_ops.llm_usage_logger import LLMUsageLogger


def audit_llm_usage_v5r1(reports_dir: str | Path = "docs/reports") -> dict:
    summary = LLMUsageLogger().aggregate()
    out_store = Path("replay_store/llm_usage")
    out_store.mkdir(parents=True, exist_ok=True)
    (out_store / "latest_llm_usage_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "latest_llm_usage_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
