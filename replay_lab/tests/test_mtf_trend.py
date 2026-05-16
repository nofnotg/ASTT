import pandas as pd

from features.mtf_trend import compute_daily_structure, compute_h4_flow, compute_weekly_bias


def _frame(rows=80):
    return pd.DataFrame({"time": pd.date_range("2026-01-01", periods=rows), "open": range(100, 100 + rows), "high": range(101, 101 + rows), "low": range(99, 99 + rows), "close": range(100, 100 + rows), "volume": [100] * rows, "trade_price": [10000] * rows})


def test_mtf_scores_and_insufficient_data():
    assert compute_weekly_bias(_frame(2))["warnings"]
    assert compute_weekly_bias(_frame(40))["weekly_bias_score"] >= 0
    assert compute_daily_structure(_frame(80))["daily_structure_score"] >= 0
    assert compute_h4_flow(_frame(80))["h4_flow_score"] >= 0
