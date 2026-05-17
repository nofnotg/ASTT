from __future__ import annotations

from features.supply_demand_zone import detect_supply_demand_zones


def detect_body_zone_clusters(frame, timeframe: str, as_of_time=None) -> list[dict]:
    return detect_supply_demand_zones(frame, timeframe=timeframe, as_of_time=as_of_time, min_bars=20, max_atr_width=3.5)
