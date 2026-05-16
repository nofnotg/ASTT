from __future__ import annotations

import pandas as pd


def detect_rs_flip(frame: pd.DataFrame, reference_zone: list[float], tolerance_pct: float = 0.5) -> dict:
    data = _normalize(frame)
    if data.empty or not reference_zone or reference_zone == [0.0, 0.0]:
        return _empty(reference_zone)
    low_zone, high_zone = reference_zone
    close = data["close"].astype(float)
    volume = data["volume"].astype(float)
    current = float(close.iloc[-1])
    tol = current * tolerance_pct / 100
    recent_close = close.tail(20)
    broke_above = bool((recent_close > high_zone).any())
    first_break_pos = list(recent_close > high_zone).index(True) if broke_above else 0
    after_break = recent_close.iloc[first_break_pos:] if broke_above else recent_close
    pullback_touched = bool((data["low"].astype(float).tail(10) <= high_zone + tol).any())
    closed_below_zone = bool((after_break.tail(8) < low_zone - tol).any())
    volume_dry_up = float(volume.tail(6).mean()) <= float(volume.tail(20).mean()) * 0.9 if len(data) >= 20 else True
    rebound_volume_expansion = float(volume.tail(2).mean()) >= float(volume.tail(8).mean()) * 0.95 if len(data) >= 8 else True
    has_rs_flip = broke_above and pullback_touched and not closed_below_zone
    score = 0.0
    if broke_above:
        score += 25
    if pullback_touched:
        score += 25
    if not closed_below_zone:
        score += 20
    if volume_dry_up:
        score += 15
    if rebound_volume_expansion:
        score += 15
    return {
        "has_rs_flip": bool(has_rs_flip),
        "reference_zone": reference_zone,
        "pullback_touched": bool(pullback_touched),
        "closed_below_zone": bool(closed_below_zone),
        "volume_dry_up": bool(volume_dry_up),
        "rebound_volume_expansion": bool(rebound_volume_expansion),
        "rs_flip_score": float(max(0.0, min(100.0, score))),
    }


def _empty(reference_zone: list[float]) -> dict:
    return {"has_rs_flip": False, "reference_zone": reference_zone, "pullback_touched": False, "closed_below_zone": False, "volume_dry_up": False, "rebound_volume_expansion": False, "rs_flip_score": 0.0}


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
