from __future__ import annotations

from typing import Any

from analysis.return_to_drawdown_analyzer import add_return_to_drawdown_decisions


def analyze_return_amplification(causal_summary: dict[str, Any]) -> dict[str, Any]:
    scenarios = [_compact(row) for row in causal_summary.get("scenarios", []) if row.get("scenario") in {"BALANCED_GROWTH", "AGGRESSIVE_GROWTH", "HIGH_OCTANE_RESEARCH"}]
    decisions = add_return_to_drawdown_decisions(scenarios)
    best_return = max(scenarios, key=lambda row: float(row.get("capital", {}).get("total_return_pct", 0.0))) if scenarios else {}
    best_ratio = max(scenarios, key=lambda row: float(row.get("capital", {}).get("return_to_mdd_ratio", 0.0))) if scenarios else {}
    rejected = [row for row, decision in zip(scenarios, decisions) if decision["decision"] in {"TOO_RISKY", "REJECT"}]
    return {
        "schema_version": "v64_return_amplification_v1",
        "scenarios": scenarios,
        "decisions": decisions,
        "best_growth_scenario": best_ratio.get("scenario"),
        "highest_return_scenario": best_return.get("scenario"),
        "best_return_mdd_ratio": best_ratio.get("capital", {}).get("return_to_mdd_ratio", 0.0),
        "rejected_high_risk_scenario": rejected[0].get("scenario") if rejected else None,
        "protected_floor_violations": sum(int(row.get("protected_floor_violations", 0)) for row in scenarios),
        "dd_cap_violations": sum(int(row.get("dd_cap_violations", 0)) for row in scenarios),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario": row.get("scenario"),
        "decision": row.get("decision"),
        "high_risk_research_only": row.get("high_risk_research_only", False),
        "capital": row.get("capital", {}),
        "skipped_trade_count": row.get("skipped_trade_count", 0),
        "protected_floor_violations": row.get("protected_floor_violations", 0),
        "dd_cap_violations": row.get("dd_cap_violations", 0),
        "lookahead_fail_count": row.get("lookahead_fail_count", 0),
    }
