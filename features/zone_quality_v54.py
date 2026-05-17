from __future__ import annotations

import pandas as pd


def compute_zone_quality_v54(zone: dict, frame, htf_zones=None, as_of_time=None) -> dict:
    data = frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame or [])
    if as_of_time is not None and not data.empty and "time" in data:
        data = data[pd.to_datetime(data["time"]) <= pd.Timestamp(as_of_time)]
    low = float(zone.get("zone_low", zone.get("low", 0.0)))
    high = float(zone.get("zone_high", zone.get("high", low)))
    mid = (low + high) / 2 if high or low else 0.0
    width_pct = (high - low) / mid * 100 if mid else 999.0
    htf_overlap = _overlap(zone, htf_zones or [])
    clean_retest = _touch_count(data, low, high) <= 2
    zone_width_ok = width_pct <= 1.5
    reaction_history_score = min(100.0, _touch_count(data, low, high) * 20.0)
    freshness_score = 70.0 if len(data) < 100 else 50.0
    breakout_impulse_score = _impulse(data)
    volume_acceptance_score = _volume_acceptance(data, low, high)
    score = (
        (20 if htf_overlap else 0)
        + (20 if clean_retest else 5)
        + (15 if zone_width_ok else 0)
        + reaction_history_score * 0.15
        + freshness_score * 0.10
        + breakout_impulse_score * 0.20
        + volume_acceptance_score * 0.20
    )
    warnings = []
    if not zone_width_ok:
        warnings.append("zone_too_wide")
    if not clean_retest:
        warnings.append("damaged_zone")
    return {
        "zone_quality_score": float(max(0.0, min(100.0, score))),
        "htf_overlap": bool(htf_overlap),
        "clean_retest": bool(clean_retest),
        "zone_width_ok": bool(zone_width_ok),
        "reaction_history_score": float(reaction_history_score),
        "freshness_score": float(freshness_score),
        "breakout_impulse_score": float(breakout_impulse_score),
        "volume_acceptance_score": float(volume_acceptance_score),
        "quality_grade": _grade(score),
        "warnings": warnings,
    }


def _overlap(zone: dict, zones: list[dict]) -> bool:
    low = float(zone.get("zone_low", 0.0))
    high = float(zone.get("zone_high", low))
    return any(float(z.get("zone_low", 0.0)) <= high and float(z.get("zone_high", 0.0)) >= low for z in zones)


def _touch_count(frame: pd.DataFrame, low: float, high: float) -> int:
    if frame.empty:
        return 0
    return int(((frame["low"].astype(float) <= high) & (frame["high"].astype(float) >= low)).sum())


def _impulse(frame: pd.DataFrame) -> float:
    if len(frame) < 2:
        return 0.0
    close = frame["close"].astype(float)
    return float(min(100.0, abs(close.iloc[-1] - close.iloc[0]) / max(close.iloc[0], 1e-9) * 500))


def _volume_acceptance(frame: pd.DataFrame, low: float, high: float) -> float:
    if frame.empty or "volume" not in frame:
        return 0.0
    inside = frame[(frame["close"].astype(float) >= low) & (frame["close"].astype(float) <= high)]
    if inside.empty:
        return 0.0
    base = float(frame["volume"].mean()) or 1.0
    return float(min(100.0, inside["volume"].mean() / base * 50))


def _grade(score: float) -> str:
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    if score >= 45:
        return "C"
    return "REJECT"
