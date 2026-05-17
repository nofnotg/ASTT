from __future__ import annotations

import pandas as pd

from features.allocation_diagnostic import build_allocation_diagnostic


def test_allocation_diagnostic_counts_and_alpha():
    trades = pd.DataFrame(
        [
            {"signal_grade": "A", "allocation_pct": 0.2, "realized_pnl_pct": 2.0, "trade_pnl_krw": 2000},
            {"signal_grade": "B", "allocation_pct": 0.8, "realized_pnl_pct": -1.0, "trade_pnl_krw": -4000},
        ]
    )
    result = build_allocation_diagnostic(trades, 500000)
    assert result["good_trade_underallocated_count"] == 1
    assert result["bad_trade_overallocated_count"] == 1
    assert result["allocation_alpha_krw"] < 0
    assert any(row["grade"] == "A" and row["entry_count"] == 1 for row in result["grade_table"])
