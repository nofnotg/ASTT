from __future__ import annotations

from analysis.v64_scenario_comparator import compare_v64_scenarios


def test_v64_scenario_comparator_builds_rows():
    summary = {
        "scenarios": [
            {"scenario": "BASELINE", "capital": {"final_equity_krw": 500000, "total_return_pct": 0, "max_drawdown_pct": -1, "profit_factor": 1, "trade_count": 1, "return_to_mdd_ratio": 0}, "lookahead_fail_count": 0}
        ]
    }

    result = compare_v64_scenarios(summary)

    assert result["scenarios"][0]["scenario"] == "BASELINE"
