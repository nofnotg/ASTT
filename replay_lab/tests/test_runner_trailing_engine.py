from __future__ import annotations

import pandas as pd

from execution.runner_trailing_engine import evaluate_trailing_stop


def test_trailing_stop_peak_drawdown_and_break_even():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=3, freq="min"), "high": [100, 104, 103], "low": [99, 102, 101], "close": [100, 103, 102]})
    trail = evaluate_trailing_stop(frame, 100, 98, "peak_drawdown_1_5")
    be = evaluate_trailing_stop(frame, 100, 98, "break_even_after_tp1", tp1_hit=True)
    assert trail["stop_price"] >= 98
    assert be["stop_price"] >= 100
