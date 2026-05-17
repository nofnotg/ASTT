from __future__ import annotations

import pandas as pd

from features.simple_exit_models import simulate_simple_exit


def test_simple_exit_fixed_rr_and_zone_target():
    frame = pd.DataFrame({"high": [101.5], "low": [100], "close": [101]})
    rr = simulate_simple_exit(frame, 100, 99, "FIXED_RR_1_0")
    zone = simulate_simple_exit(frame, 100, 99, "ZONE_TARGET_FULL_EXIT", {"target_1": 101.2})
    assert rr["exit_reason"] == "TAKE_PROFIT"
    assert zone["hit_target"] is True


def test_simple_exit_stop_first_and_time_stop():
    stop = simulate_simple_exit(pd.DataFrame({"high": [100.2], "low": [98.8], "close": [99]}), 100, 99, "FIXED_RR_1_5")
    quiet = simulate_simple_exit(pd.DataFrame({"high": [100.2], "low": [99.5], "close": [100.1]}), 100, 99, "FIXED_RR_1_5")
    assert stop["exit_reason"] == "STOP_LOSS"
    assert quiet["exit_reason"] == "TIME_STOP"


def test_simple_exit_tp1_break_even():
    frame = pd.DataFrame({"high": [101.1, 101.0], "low": [100.2, 99.9], "close": [100.5, 100.0]})
    result = simulate_simple_exit(frame, 100, 99, "TP1_BREAK_EVEN")
    assert result["exit_reason"] == "BREAK_EVEN"
