import pandas as pd
from features.supply_demand_zone import detect_supply_demand_zones


def test_zone_calculation_excludes_future_candles():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=50, freq="min"), "open": [100] * 50, "high": [101] * 49 + [999], "low": [99] * 50, "close": [100] * 50, "volume": [100] * 50})
    as_of = frame["time"].iloc[30]
    zones = detect_supply_demand_zones(frame, "1m", as_of_time=as_of, min_bars=10)
    assert all(pd.Timestamp(zone["end_time"]) <= as_of for zone in zones if zone["end_time"])
    assert all(zone["zone_high"] < 999 for zone in zones)
