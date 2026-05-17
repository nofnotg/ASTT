from __future__ import annotations

import pandas as pd


def label_zone_reaction(
    frame: pd.DataFrame,
    zone: dict,
    touch_time,
    direction: str,
    horizons=(5, 10, 20, 40),
    r_multiple: float = 1.0,
) -> dict:
    """Label post-touch reaction using only candles after touch_time."""

    if frame is None or frame.empty:
        return _empty(zone, touch_time, direction, "NO_REACTION")
    data = frame.copy()
    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    after = data[data["time"] > pd.Timestamp(touch_time)].head(max(horizons)).copy()
    if after.empty:
        return _empty(zone, touch_time, direction, "NO_REACTION")

    zone_low = float(zone.get("zone_low", zone.get("low", 0.0)))
    zone_high = float(zone.get("zone_high", zone.get("high", zone_low)))
    entry = zone_high if direction.upper() in {"DEMAND", "LONG", "BOUNCE"} else zone_low
    risk = max(abs(zone_high - zone_low), entry * 0.003)
    if direction.upper() in {"DEMAND", "LONG", "BOUNCE"}:
        mfe_pct = (float(after["high"].max()) - entry) / entry * 100
        mae_pct = (float(after["low"].min()) - entry) / entry * 100
        hit_1r = float(after["high"].max()) >= entry + risk * r_multiple
        hit_stop = float(after["low"].min()) <= zone_low - risk * 0.1
        label = _long_label(hit_1r, hit_stop, after, zone_low, zone_high)
    else:
        mfe_pct = (entry - float(after["low"].min())) / entry * 100
        mae_pct = (entry - float(after["high"].max())) / entry * 100
        hit_1r = float(after["low"].min()) <= entry - risk * r_multiple
        hit_stop = float(after["high"].max()) >= zone_high + risk * 0.1
        label = _short_label(hit_1r, hit_stop, after, zone_low, zone_high)

    return {
        "zone_id": zone.get("zone_id", ""),
        "market": zone.get("market", ""),
        "timeframe": zone.get("timeframe", ""),
        "touch_time": pd.Timestamp(touch_time).isoformat(),
        "reaction_label": label,
        "horizon_bars": int(len(after)),
        "mfe_pct": float(mfe_pct),
        "mae_pct": float(mae_pct),
        "hit_1r": bool(hit_1r),
        "hit_stop": bool(hit_stop),
        "time_to_reaction_bars": _time_to_reaction(after, entry, risk, direction),
        "zone_strength": float(zone.get("strength", 0.0)),
        "zone_width_pct": float(zone.get("zone_width_pct", 0.0)),
    }


def _long_label(hit_1r: bool, hit_stop: bool, after: pd.DataFrame, zone_low: float, zone_high: float) -> str:
    closes = after["close"].astype(float)
    if hit_1r and not hit_stop:
        return "BOUNCE_SUCCESS"
    if hit_stop and closes.iloc[-1] < zone_low:
        return "BREAKDOWN_FAIL"
    if after["high"].max() >= zone_high and after["low"].min() <= zone_low:
        return "CHOP"
    return "NO_REACTION"


def _short_label(hit_1r: bool, hit_stop: bool, after: pd.DataFrame, zone_low: float, zone_high: float) -> str:
    closes = after["close"].astype(float)
    if hit_1r and not hit_stop:
        return "REJECTION_SUCCESS"
    if hit_stop and closes.iloc[-1] > zone_high:
        return "BREAKOUT_SUCCESS"
    if after["high"].max() >= zone_high and after["low"].min() <= zone_low:
        return "CHOP"
    return "NO_REACTION"


def _time_to_reaction(after: pd.DataFrame, entry: float, risk: float, direction: str) -> int:
    target = entry + risk if direction.upper() in {"DEMAND", "LONG", "BOUNCE"} else entry - risk
    for idx, row in enumerate(after.to_dict("records"), start=1):
        if direction.upper() in {"DEMAND", "LONG", "BOUNCE"} and float(row["high"]) >= target:
            return idx
        if direction.upper() not in {"DEMAND", "LONG", "BOUNCE"} and float(row["low"]) <= target:
            return idx
    return 0


def _empty(zone: dict, touch_time, direction: str, label: str) -> dict:
    return {
        "zone_id": zone.get("zone_id", ""),
        "market": zone.get("market", ""),
        "timeframe": zone.get("timeframe", ""),
        "touch_time": pd.Timestamp(touch_time).isoformat(),
        "reaction_label": label,
        "horizon_bars": 0,
        "mfe_pct": 0.0,
        "mae_pct": 0.0,
        "hit_1r": False,
        "hit_stop": False,
        "time_to_reaction_bars": 0,
        "zone_strength": float(zone.get("strength", 0.0)),
        "zone_width_pct": float(zone.get("zone_width_pct", 0.0)),
    }
