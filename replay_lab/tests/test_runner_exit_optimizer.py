from __future__ import annotations

import pandas as pd

from features.runner_exit_optimizer import simulate_runner_exit


def test_runner_exit_tp_and_contribution():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=4, freq="min"), "open": [100] * 4, "high": [101, 102, 104, 103], "low": [99.5, 101, 102, 102], "close": [101, 102, 103, 103]})
    result = simulate_runner_exit(frame, 100, 99, {"runner_model": "BALANCED_RUNNER"}, {"target_1": 101, "target_2": 102, "target_3": 104}, "peak_drawdown_2_0")
    assert result["tp1_hit"] is True
    assert result["tp2_hit"] is True
    assert result["runner_contribution_pct"] > 0
    assert result["capture_ratio"] > 0
