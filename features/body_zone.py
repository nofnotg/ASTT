from __future__ import annotations

import pandas as pd


def detect_body_zones(frame: pd.DataFrame, volume_multiplier: float = 2.0, lookback: int = 120) -> list[dict]:
    data = _normalize(frame).tail(lookback).copy()
    if data.empty or "volume" not in data:
        return []
    avg_volume = float(data["volume"].astype(float).mean()) or 1.0
    heavy = data[data["volume"].astype(float) >= avg_volume * volume_multiplier].copy()
    if heavy.empty:
        heavy = data.nlargest(min(8, len(data)), "volume").copy()
    zones = []
    for _, row in heavy.iterrows():
        body_low = min(float(row["open"]), float(row["close"]))
        body_high = max(float(row["open"]), float(row["close"]))
        zones.append(
            {
                "low": body_low,
                "high": body_high,
                "mid": (body_low + body_high) / 2,
                "volume": float(row.get("volume", 0.0)),
                "time": str(row.get("time", "")),
                "zone_type": "HEAVY_BODY",
            }
        )
    return sorted(zones, key=lambda zone: zone["volume"], reverse=True)


def nearest_body_support(price: float, zones: list[dict]) -> dict:
    supports = [zone for zone in zones if zone["low"] <= price]
    if not supports:
        return _empty_zone(price)
    zone = min(supports, key=lambda item: abs(price - item["high"]))
    return {
        "support_zone": [zone["low"], zone["high"]],
        "distance_to_support_pct": _distance_pct(price, [zone["low"], zone["high"]]),
        "body_zone_score": _support_score(price, [zone["low"], zone["high"]]),
    }


def nearest_body_resistance(price: float, zones: list[dict]) -> dict:
    resistances = [zone for zone in zones if zone["high"] > price]
    if not resistances:
        return {"resistance_zone": [0.0, 0.0], "target_space_pct": 999.0}
    zone = min(resistances, key=lambda item: abs(item["low"] - price))
    target_space = (zone["low"] - price) / price * 100 if price else 0.0
    return {"resistance_zone": [zone["low"], zone["high"]], "target_space_pct": float(target_space)}


def body_zone_summary(frame: pd.DataFrame, price: float | None = None) -> dict:
    data = _normalize(frame)
    if data.empty:
        return _empty_zone(0.0)
    current = float(price if price is not None else data.iloc[-1]["close"])
    zones = detect_body_zones(data)
    support = nearest_body_support(current, zones)
    resistance = nearest_body_resistance(current, zones)
    score = support["body_zone_score"]
    if resistance["target_space_pct"] >= 1.2:
        score += 20
    elif resistance["target_space_pct"] < 0.5:
        score -= 20
    return {
        **support,
        **resistance,
        "zones": zones[:12],
        "target_space_pct": float(resistance["target_space_pct"]),
        "body_zone_score": max(0.0, min(100.0, score)),
    }


def calculate_body_zones(frame: pd.DataFrame, volume_multiplier: float = 2.0, lookback: int = 120) -> dict:
    zones = detect_body_zones(frame, volume_multiplier=volume_multiplier, lookback=lookback)
    return {"zones": [{"low": zone["low"], "high": zone["high"], "mid": zone["mid"], "volume": zone["volume"], "time": zone["time"]} for zone in zones]}


def detect_rs_flip(frame: pd.DataFrame, zone: dict | None) -> dict:
    if frame is None or frame.empty or not zone:
        return {"state": "NONE", "score": 0.0}
    close = frame["close"].astype(float)
    high = float(zone.get("high", 0.0) or 0.0)
    low = float(zone.get("low", 0.0) or 0.0)
    if not high or not low:
        return {"state": "NONE", "score": 0.0}
    current = float(close.iloc[-1])
    if current > high:
        state = "BREAKOUT"
    elif low <= current <= high:
        state = "RETEST"
    elif current >= high * 0.995:
        state = "PRE_BREAKOUT"
    else:
        state = "NONE"
    return {"state": state, "score": 70.0 if state != "NONE" else 0.0, "zone": zone}


def target_space_pct(current_price: float, target_price: float) -> float:
    return (float(target_price) - float(current_price)) / float(current_price) * 100 if current_price else 0.0


def _support_score(price: float, zone: list[float]) -> float:
    distance = _distance_pct(price, zone)
    if distance <= 0.3:
        return 70.0
    if distance <= 0.7:
        return 55.0
    if distance <= 1.2:
        return 40.0
    return 15.0


def _distance_pct(price: float, zone: list[float]) -> float:
    if not price or not zone or zone == [0.0, 0.0]:
        return 999.0
    low, high = zone
    if low <= price <= high:
        return 0.0
    anchor = high if price > high else low
    return abs(price - anchor) / price * 100


def _empty_zone(price: float) -> dict:
    return {
        "support_zone": [0.0, 0.0],
        "resistance_zone": [0.0, 0.0],
        "distance_to_support_pct": 999.0,
        "target_space_pct": 0.0 if price else 0.0,
        "body_zone_score": 0.0,
        "zones": [],
    }


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
