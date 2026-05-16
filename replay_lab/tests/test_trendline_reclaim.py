import pandas as pd

from features.trendline_reclaim import detect_trendline_bounce, detect_trendline_break_reclaim


def test_trendline_reclaim_scores():
    frame = pd.DataFrame({"open": range(100, 130), "high": range(101, 131), "low": range(99, 129), "close": range(100, 130), "volume": [100] * 30})
    assert detect_trendline_break_reclaim(frame)["trendline_score"] >= 0
    assert detect_trendline_bounce(frame)["trendline_score"] >= 0
