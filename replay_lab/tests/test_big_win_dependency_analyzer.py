from __future__ import annotations

from analysis.big_win_dependency_analyzer import analyze_big_win_dependency


def test_big_win_dependency_reports_top_contribution():
    trades = [
        {"trade_id": "w1", "pnl_krw": 10000, "return_pct": 5},
        {"trade_id": "l1", "pnl_krw": -1000, "return_pct": -1},
    ]
    result = analyze_big_win_dependency("S", trades)
    assert result["top_1_win_contribution_pct"] > 100
    assert result["dependency_decision"] in {"FAT_TAIL_ACCEPTABLE", "FAT_TAIL_FRAGILE", "RANDOM_SPIKE_SUSPECTED"}
