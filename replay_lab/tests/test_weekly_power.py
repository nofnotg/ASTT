import pandas as pd
from features.weekly_power import compute_weekly_power


def test_weekly_power_states():
    completed = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=3, freq="W"), "open": [100, 110, 120], "high": [120, 130, 140], "low": [90, 100, 110], "close": [115, 125, 135]})
    current = pd.DataFrame({"time": [pd.Timestamp("2026-01-25")], "open": [135], "high": [150], "low": [130], "close": [145]})
    result = compute_weekly_power(completed, current, pd.DataFrame())
    assert result["completed_week_bias"] == "BULL"
    assert result["current_week_candle"] == "BULL"
