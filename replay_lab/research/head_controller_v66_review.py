from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v66_review(
    reports_dir: str = "docs/reports",
    llm_provider: str = "openai",
) -> dict[str, Any]:
    root = Path(reports_dir)
    comparison = _read(root / "latest_v66_btcd_scenario_comparison_summary.json")
    recommendation = comparison.get("recommendation", {})
    scenarios = comparison.get("scenarios", [])
    rejected = [row.get("scenario") for row in scenarios if row.get("decision") == "BTCD_FILTER_REJECTED"]
    review = {
        "schema_version": "head_controller_v66_review_v1",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_scenario": recommendation.get("best_scenario", "NONE"),
        "rejected_scenarios": rejected,
        "forward_candidates": recommendation.get("forward_candidates", []),
        "research_only_candidates": recommendation.get("research_only_candidates", ["SHORT_HEDGE_BTCD_RESEARCH"]),
        "primary_improvement": "BTC Dominance overlay is considered only if saved loss exceeds missed profit and return/MDD improves.",
        "primary_risk": "Global BTC Dominance may be unavailable; Upbit BTC Flow Dominance Proxy is not the same as global dominance.",
        "next_experiments": [
            "Do not modify existing Rolling/Balanced baselines.",
            "Carry only validated BTCD overlays into forward paper.",
            "Keep Short/Hedge as paper research only.",
            "Add real spread/depth overlay before any live discussion.",
        ],
        "risk_flags": ["LIVE_NOT_ALLOWED", "PAPER_ONLY", "NO_AUTO_APPLY", "GLOBAL_BTCD_MAY_BE_UNAVAILABLE"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v66_review_summary.json", review)
    return review


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

