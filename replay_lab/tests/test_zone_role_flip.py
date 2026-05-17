import pandas as pd
from features.zone_role_flip import detect_zone_role_flip


def test_zone_role_flip_bounce_and_failed():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=8, freq="min"), "open": [99, 101, 102, 101, 102, 103, 102, 104], "high": [100, 103, 104, 102, 104, 105, 103, 105], "low": [98, 100, 101, 100, 101, 102, 101, 103], "close": [99, 102, 103, 101.5, 103, 104, 102.5, 104.5], "volume": [100, 200, 150, 120, 180, 220, 160, 240]})
    assert detect_zone_role_flip(frame, {"zone_low": 100, "zone_high": 101})["role_flip_state"] in {"RETEST", "BOUNCE", "BREAKOUT"}
    failed = frame.copy()
    failed.loc[7, "close"] = 98
    assert detect_zone_role_flip(failed, {"zone_low": 100, "zone_high": 101})["role_flip_state"] == "FAILED"
