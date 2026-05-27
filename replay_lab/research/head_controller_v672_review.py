from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v672_review(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v672_btcdom_index_scenario_summary.json")
    scenarios = scenario.get("scenarios", [])
    candidate_rows = [
        row
        for row in scenarios
        if row.get("decision") in {"BTCDOM_INDEX_FILTER_VALIDATED", "BTCDOM_RELATIVE_STRENGTH_CANDIDATE"}
    ]
    candidates = [row.get("scenario") for row in candidate_rows]
    rejected = [row.get("scenario") for row in scenarios if row.get("scenario") != "CONTROL_EXISTING" and row.get("scenario") not in candidates]
    best_row = max(
        candidate_rows,
        key=lambda row: (float(row.get("return_mdd_ratio") or 0.0), float(row.get("final_equity_krw") or 0.0)),
        default={},
    )
    best = best_row.get("scenario", "")
    payload = {
        "schema_version": "head_controller_v672_review_v1",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_scenario": best,
        "rejected_scenarios": rejected,
        "forward_candidates": candidates,
        "primary_problem": "NO_VALID_BTCDOM_INDEX_SCENARIO" if not candidates else "FORWARD_PAPER_REQUIRED",
        "risk_flags": ["LIVE_NOT_ALLOWED", "PAPER_ONLY", "NO_AUTO_APPLY", "BTCDOM_INDEX_IS_NOT_PERCENTAGE"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v672_review_summary.json", payload)
    return payload


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
