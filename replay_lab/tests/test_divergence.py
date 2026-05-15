import pandas as pd

from features.divergence import detect_bullish_fear_divergence, find_fear_peaks, find_swing_lows


def test_bullish_fear_divergence_detects_lower_low_lower_fear():
    lows = [10, 9, 8, 9, 10, 8.5, 7.5, 8.5, 9]
    fear = [20, 80, 40, 20, 20, 55, 35, 20, 15]
    frame = pd.DataFrame({"time": range(len(lows)), "open": lows, "high": [x + 1 for x in lows], "low": lows, "close": [x + 0.5 for x in lows], "fear_score": fear})
    assert len(find_swing_lows(frame, 1, 1)) >= 2
    assert len(find_fear_peaks(frame, 1, 1)) >= 2
    result = detect_bullish_fear_divergence(frame, min_price_lower_low_pct=0.3, max_fear_peak_ratio=0.9, left=1, right=1)
    assert result["has_bullish_fear_divergence"]
    assert result["divergence_strength"] > 0
