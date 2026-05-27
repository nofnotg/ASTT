from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v67_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v67_global_btcd_scenario_summary.json")
    rejected = _read(root / "latest_v67_global_btcd_rejected_scenarios_summary.json")
    candidates = [row.get("scenario") for row in rejected.get("kept_candidates", [])]
    data_required = not scenario.get("full_period_validation_possible", False)
    summary = {
        "schema_version": "head_controller_v67_review_v1",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_scenario": candidates[0] if candidates else "",
        "rejected_scenarios": [row.get("scenario") for row in rejected.get("rejected_scenarios", [])],
        "forward_candidates": candidates,
        "primary_problem": "GLOBAL_BTCD_DATA_REQUIRED" if data_required else "GLOBAL_BTCD_FILTER_REVIEW_REQUIRED",
        "risk_flags": ["LIVE_NOT_ALLOWED", "PAPER_ONLY", "NO_AUTO_APPLY"] + (["GLOBAL_BTCD_HISTORY_MISSING"] if data_required else []),
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    path = root / "latest_head_controller_v67_review_summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
