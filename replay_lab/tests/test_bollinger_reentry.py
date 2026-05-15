import pandas as pd

from features.bollinger_reentry import detect_lower_band_reentry


def test_lower_band_reentry_detects_break_and_close_inside():
    close = [100.0] * 30 + [92.0, 98.0]
    low = [99.0] * 30 + [88.0, 91.0]
    frame = pd.DataFrame({"time": range(len(close)), "open": close, "high": [x + 1 for x in close], "low": low, "close": close, "volume": [100] * len(close)})
    result = detect_lower_band_reentry(frame, length=30, stddev=2.0, lookback=2)
    assert result["reentered_lower_band"]
    assert result["reentry_strength"] > 0
