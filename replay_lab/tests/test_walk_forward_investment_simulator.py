from __future__ import annotations

import pandas as pd

from portfolio.walk_forward_investment_simulator import _execute_candidates


def test_walk_forward_execution_records_no_lookahead_and_equity_flow():
    exit_frame = pd.DataFrame(
        {
            "time": pd.to_datetime(["2026-01-01 02:00:00"]),
            "high": [110.0],
            "low": [99.0],
            "close": [108.0],
        }
    )
    candidates = [
        {
            "market": "KRW-AAA",
            "strategy": "ICT_FVG_OB_SWEEP",
            "setup_type": "FVG_LIQUIDITY_SWEEP",
            "entry_price": 100.0,
            "stop_price": 98.0,
            "target_price": 106.0,
            "entry_time": "2026-01-01 01:00:00",
            "signal_time": "2026-01-01 01:00:00",
            "feature_cutoff_time": "2026-01-01 01:00:00",
            "exit_plan_frame": exit_frame,
        }
    ]

    journal = _execute_candidates(candidates, initial_cash=500000, max_open_positions=3)

    assert len(journal) == 1
    trade = journal[0]
    assert trade["lookahead_check"] == "PASS"
    assert trade["used_future_data"] is False
    assert trade["feature_cutoff_time"] <= trade["entry_time"]
    assert trade["position_krw"] <= trade["equity_before"]
    assert trade["real_order_enabled"] is False
    assert trade["live_order_allowed"] is False
    assert trade["result"] == "WIN"
