import pandas as pd

from features.rs_flip import detect_rs_flip


def test_rs_flip_detects_retest_and_breakdown():
    frame = pd.DataFrame({"open": [99, 101, 102, 101, 102], "high": [100, 103, 103, 102, 104], "low": [98, 100, 101, 100.5, 101], "close": [99, 102, 102.5, 101.5, 103], "volume": [200, 300, 150, 120, 250]})
    assert detect_rs_flip(frame, [100, 101])["has_rs_flip"]
    broken = frame.copy()
    broken.loc[4, "close"] = 98
    assert not detect_rs_flip(broken, [100, 101])["has_rs_flip"]
