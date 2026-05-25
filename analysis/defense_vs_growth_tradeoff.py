from __future__ import annotations

from typing import Any


def summarize_defense_growth_tradeoff(causal_summary: dict[str, Any]) -> dict[str, Any]:
    scenarios = causal_summary.get("scenarios", [])
    baseline = next((row for row in scenarios if row.get("scenario") == "BASELINE"), {})
    balanced = next((row for row in scenarios if row.get("scenario") == "BALANCED_GROWTH"), {})
    aggressive = next((row for row in scenarios if row.get("scenario") == "AGGRESSIVE_GROWTH"), {})
    return {
        "baseline_return_pct": baseline.get("capital", {}).get("total_return_pct", 0.0),
        "balanced_return_pct": balanced.get("capital", {}).get("total_return_pct", 0.0),
        "aggressive_return_pct": aggressive.get("capital", {}).get("total_return_pct", 0.0),
        "baseline_mdd_pct": baseline.get("capital", {}).get("max_drawdown_pct", 0.0),
        "balanced_mdd_pct": balanced.get("capital", {}).get("max_drawdown_pct", 0.0),
        "aggressive_mdd_pct": aggressive.get("capital", {}).get("max_drawdown_pct", 0.0),
    }
