import pandas as pd

from features.trendline import detect_trendline_bounce, fit_support_trendline


def test_support_trendline_and_bounce_detection():
    swings = [{"index": 0, "low": 10.0}, {"index": 5, "low": 10.5}, {"index": 10, "low": 11.0}]
    line = fit_support_trendline(swings)
    assert line["has_support_trendline"]
    lows = [10, 11, 10.2, 11, 10.5, 11.3, 10.8, 11.5, 11.1, 11.7, 11.4, 12.0, 11.65]
    frame = pd.DataFrame({"time": range(len(lows)), "open": [x + 0.2 for x in lows], "high": [x + 0.7 for x in lows], "low": lows, "close": [x + 0.4 for x in lows], "volume": [100] * len(lows)})
    result = detect_trendline_bounce(frame, tolerance_pct=5)
    assert "trendline_score" in result
