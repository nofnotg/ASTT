import pandas as pd
from features.supply_demand_zone import detect_supply_demand_zones


def test_supply_demand_zone_body_based_as_of():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=40, freq="min"), "open": [100] * 40, "high": [102] * 40, "low": [99] * 40, "close": [101] * 40, "volume": [100] * 40})
    zones = detect_supply_demand_zones(frame, "15m", as_of_time=frame["time"].iloc[25], min_bars=10)
    assert zones
    assert all(pd.Timestamp(z["end_time"]) <= frame["time"].iloc[25] for z in zones if z["end_time"])
