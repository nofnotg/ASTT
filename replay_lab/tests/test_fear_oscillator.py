import pandas as pd

from features.fear_oscillator import classify_fear_zone, compute_fear_oscillator, latest_fear


def test_fear_oscillator_outputs_score_and_zone():
    frame = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=40, freq="5min"),
            "open": [100] * 40,
            "high": [101] * 40,
            "low": [99] * 39 + [88],
            "close": [100] * 40,
            "volume": [100] * 39 + [500],
        }
    )
    data = compute_fear_oscillator(frame, 30)
    fear = latest_fear(frame, 30)
    assert "vix_fix" in data
    assert 0 <= fear["fear_score"] <= 100
    assert classify_fear_zone(75) == "PANIC"
