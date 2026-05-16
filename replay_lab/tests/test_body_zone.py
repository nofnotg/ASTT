import pandas as pd

from features.body_zone import body_zone_summary, detect_body_zones, nearest_body_resistance, nearest_body_support


def test_body_zone_support_resistance():
    frame = pd.DataFrame({"open": [100, 101, 102], "close": [101, 102, 103], "high": [102, 103, 104], "low": [99, 100, 101], "volume": [100, 500, 100], "time": [1, 2, 3]})
    zones = detect_body_zones(frame, volume_multiplier=1.5)
    assert zones
    assert nearest_body_support(102.5, zones)["distance_to_support_pct"] >= 0
    assert nearest_body_resistance(100.5, zones)["target_space_pct"] >= 0
    assert body_zone_summary(frame, 102.5)["body_zone_score"] >= 0
