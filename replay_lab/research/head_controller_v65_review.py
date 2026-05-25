from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_head_controller_v65_review(
    reports_dir: str = "docs/reports",
    llm_provider: str = "openai",
) -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v65_ma_scenario_summary.json")
    recommendation = scenario.get("recommendation", {})
    best = recommendation.get("best_scenario", "NONE")
    judgement = recommendation.get("final_judgement", "MA_FILTER_REJECTED")
    attribution = scenario.get("ma_condition_attribution", [])
    rejected = [row.get("ma_condition") for row in attribution if row.get("decision") == "DISABLE"]
    quality = [row.get("ma_condition") for row in attribution if row.get("decision") == "KEEP_AS_QUALITY_SCORE"]
    review = {
        "schema_version": "head_controller_v65_review_v1",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "llm_provider": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "best_scenario": best,
        "forward_candidate": "NONE",
        "rejected_scenario": "MA_FILTER_ONLY, MA_POLICY_ROUTER, MA_DEFENSIVE_REPAIR",
        "recommended_policy": "KEEP_CURRENT_BALANCED_GROWTH_BASELINE",
        "next_forward_candidate": "NONE",
        "validated_filters": [],
        "rejected_filters": rejected,
        "research_only_filters": quality,
        "primary_improvement": "None. MA hard filters reduced drawdown but destroyed too much return and did not repair 2025/2026.",
        "primary_risk": "MA conditions that looked defensive also contained many profitable ICT/Combined trades, especially in 2023/2024.",
        "next_experiments": [
            "Disable MA hard no-trade filters.",
            "Keep squeeze/alignment only as non-binding diagnostics.",
            "Focus V6.6 on market/coin cooldown, monthly loss limits, and defensive A+ setup gating.",
        ],
        "risk_flags": [
            "LIVE_NOT_ALLOWED",
            "MA is used only as filter/router, not standalone buy trigger",
            "V6.5 MA hard filter rejected",
            "OHLCV-only validation still needs spread/depth forward overlay",
        ],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "real_order_enabled": False,
    }
    _write(root / "latest_head_controller_v65_review_summary.json", review)
    return review


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
