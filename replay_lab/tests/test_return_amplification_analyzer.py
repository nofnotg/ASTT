from __future__ import annotations

from analysis.return_amplification_analyzer import analyze_return_amplification


def test_return_amplification_analyzer_selects_highest_return():
    result = analyze_return_amplification(
        {
            "scenarios": [
                {"scenario": "BALANCED_GROWTH", "capital": {"total_return_pct": 10, "return_to_mdd_ratio": 2, "max_drawdown_pct": -5}},
                {"scenario": "AGGRESSIVE_GROWTH", "capital": {"total_return_pct": 20, "return_to_mdd_ratio": 3, "max_drawdown_pct": -7}},
            ]
        }
    )

    assert result["highest_return_scenario"] == "AGGRESSIVE_GROWTH"
