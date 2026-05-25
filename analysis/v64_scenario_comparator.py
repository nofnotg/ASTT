from __future__ import annotations

from typing import Any

from analysis.return_to_drawdown_analyzer import add_return_to_drawdown_decisions


def compare_v64_scenarios(causal_summary: dict[str, Any]) -> dict[str, Any]:
    scenarios = causal_summary.get("scenarios", [])
    decisions = {row["scenario"]: row["decision"] for row in add_return_to_drawdown_decisions(scenarios)}
    rows = []
    for scenario in scenarios:
        capital = scenario.get("capital", {})
        rows.append(
            {
                "scenario": scenario.get("scenario"),
                "final_equity_krw": capital.get("final_equity_krw", 0.0),
                "return_pct": capital.get("total_return_pct", 0.0),
                "mdd_pct": capital.get("max_drawdown_pct", 0.0),
                "profit_factor": capital.get("profit_factor", 0.0),
                "trades": capital.get("trade_count", 0),
                "return_mdd_ratio": capital.get("return_to_mdd_ratio", 0.0),
                "lookahead_fail_count": scenario.get("lookahead_fail_count", 0),
                "decision": decisions.get(scenario.get("scenario"), scenario.get("decision")),
            }
        )
    return {
        "schema_version": "v64_scenario_comparison_v1",
        "scenarios": rows,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
