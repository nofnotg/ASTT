import pandas as pd

from ict_strategy.fvg_detector import detect_fvg


def test_fvg_detector_detects_bullish_gap():
    frame = pd.DataFrame({"time": [1, 2, 3], "high": [100, 101, 110], "low": [90, 95, 105], "open": [95, 98, 106], "close": [96, 100, 108], "volume": [1, 1, 1]})
    assert any(zone["zone_type"] == "BULLISH_FVG" for zone in detect_fvg(frame))
