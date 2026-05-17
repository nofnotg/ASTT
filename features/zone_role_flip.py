from __future__ import annotations

import pandas as pd


def detect_zone_role_flip(frame, zone, as_of_time=None, tolerance_pct: float = 0.5) -> dict:
    data = _as_of(_normalize(frame), as_of_time)
    if data.empty or not zone:
        return _empty(zone)
    low = float(zone.get("zone_low", zone.get("low", 0.0)))
    high = float(zone.get("zone_high", zone.get("high", 0.0)))
    mid = (low + high) / 2
    if not low or not high:
        return _empty(zone)
    close = data["close"].astype(float).tail(24)
    volume = data["volume"].astype(float).tail(24)
    tol = high * tolerance_pct / 100
    broke = bool((close > high + tol).any())
    broke_pos = list(close > high + tol).index(True) if broke else 0
    after = close.iloc[broke_pos:] if broke else close
    pullback = bool((data["low"].astype(float).tail(12) <= high + tol).any() or (data["low"].astype(float).tail(12) <= mid + tol).any())
    failed = bool((after < low - tol).any())
    dry = float(volume.tail(8).mean()) <= float(volume.mean()) * 0.95 if len(volume) else False
    expand = float(volume.tail(2).mean()) >= float(volume.tail(8).mean()) * 0.95 if len(volume) >= 8 else False
    if failed:
        state = "FAILED"
    elif broke and pullback and expand:
        state = "BOUNCE"
    elif broke and pullback:
        state = "RETEST"
    elif broke:
        state = "BREAKOUT"
    elif low <= float(close.iloc[-1]) <= high:
        state = "INSIDE_ZONE"
    else:
        state = "NONE"
    score = (25 if broke else 0) + (25 if pullback else 0) + (20 if not failed else 0) + (15 if dry else 0) + (15 if expand else 0)
    return {"role_flip_state": state, "has_rs_flip": state in {"RETEST", "BOUNCE"}, "flip_zone": zone, "pullback_touched": pullback, "closed_below_zone": failed, "volume_dry_up": dry, "rebound_volume_expansion": expand, "role_flip_score": float(max(0.0, min(100.0, score)))}


def _empty(zone) -> dict:
    return {"role_flip_state": "NONE", "has_rs_flip": False, "flip_zone": zone or {}, "pullback_touched": False, "closed_below_zone": False, "volume_dry_up": False, "rebound_volume_expansion": False, "role_flip_score": 0.0}


def _as_of(frame: pd.DataFrame, as_of_time) -> pd.DataFrame:
    if frame.empty or as_of_time is None or "time" not in frame:
        return frame
    return frame[pd.to_datetime(frame["time"]) <= pd.Timestamp(as_of_time)].copy()


def _normalize(frame) -> pd.DataFrame:
    if frame is None or getattr(frame, "empty", True):
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
