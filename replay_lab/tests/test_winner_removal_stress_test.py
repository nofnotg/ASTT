from __future__ import annotations

from analysis.winner_removal_stress_test import remove_top_winners


def test_winner_removal_stress_test_removes_largest_win():
    trades = [{"trade_id": "w", "pnl_krw": 1000, "return_pct": 2}, {"trade_id": "l", "pnl_krw": -500, "return_pct": -1}]
    result = remove_top_winners(trades, 1)
    assert result["trade_count"] == 1
    assert result["total_pnl_krw"] == -500
