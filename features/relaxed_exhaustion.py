from __future__ import annotations

import pandas as pd

from features.support_resistance import body_zone_context


def detect_drop_event(frame: pd.DataFrame, lookback: int = 12, min_drop_pct: float = 1.0) -> dict:
    data = _normalize(frame).tail(lookback)
    if data.empty:
        return {"has_drop_event": False, "drop_start_time": None, "drop_low_time": None, "drop_pct": 0.0, "drop_speed_score": 0.0}
    high_idx = data["high"].astype(float).idxmax()
    after_high = data.loc[high_idx:]
    low_idx = after_high["low"].astype(float).idxmin()
    high = float(data.loc[high_idx, "high"])
    low = float(data.loc[low_idx, "low"])
    drop_pct = (high - low) / high * 100 if high else 0.0
    bars = max(1, int(data.index.get_loc(low_idx) - data.index.get_loc(high_idx) + 1)) if low_idx in data.index and high_idx in data.index else lookback
    speed = min(100.0, drop_pct / max(bars, 1) * 60)
    return {
        "has_drop_event": bool(drop_pct >= min_drop_pct),
        "drop_start_time": str(data.loc[high_idx].get("time", "")),
        "drop_low_time": str(data.loc[low_idx].get("time", "")),
        "drop_pct": float(drop_pct),
        "drop_speed_score": float(max(0.0, min(100.0, speed))),
    }


def detect_low_retest_or_lower_low(frame: pd.DataFrame, tolerance_pct: float = 0.3, min_lower_low_pct: float = 0.3) -> dict:
    data = _normalize(frame)
    if len(data) < 6:
        return {"pattern": "NONE", "low_1": 0.0, "low_2": 0.0, "low_delta_pct": 0.0, "low_structure_score": 0.0}
    midpoint = len(data) // 2
    low_1 = float(data.iloc[:midpoint]["low"].min())
    low_2 = float(data.iloc[midpoint:]["low"].min())
    low_delta_pct = (low_1 - low_2) / low_1 * 100 if low_1 else 0.0
    if low_delta_pct >= min_lower_low_pct:
        pattern = "LOWER_LOW"
        score = min(100.0, 60 + low_delta_pct * 20)
    elif abs(low_delta_pct) <= tolerance_pct:
        pattern = "LOW_RETEST"
        score = max(35.0, 70 - abs(low_delta_pct) * 40)
    else:
        pattern = "NONE"
        score = 0.0
    return {"pattern": pattern, "low_1": low_1, "low_2": low_2, "low_delta_pct": float(low_delta_pct), "low_structure_score": float(score)}


def detect_fear_cooling(
    frame: pd.DataFrame,
    fear_col: str = "fear_score",
    volume_panic_col: str = "volume_panic",
    volatility_fear_col: str = "volatility_fear",
    cooling_ratio: float = 0.95,
) -> dict:
    data = _normalize(frame)
    if len(data) < 6:
        return _empty_cooling()
    midpoint = len(data) // 2
    first = data.iloc[:midpoint]
    second = data.iloc[midpoint:]
    fear_1, fear_2 = _max(first, fear_col), _max(second, fear_col)
    vol_1, vol_2 = _max(first, volume_panic_col), _max(second, volume_panic_col)
    tr_1, tr_2 = _max(first, volatility_fear_col), _max(second, volatility_fear_col)
    checks = []
    if fear_1 and fear_2 <= fear_1 * cooling_ratio:
        checks.append("FEAR_SCORE")
    if vol_1 and vol_2 <= vol_1 * 0.90:
        checks.append("VOLUME_PANIC")
    if tr_1 and tr_2 <= tr_1 * 0.90:
        checks.append("VOLATILITY_FEAR")
    cooling_type = "MIXED" if len(checks) > 1 else (checks[0] if checks else "NONE")
    score = 0.0
    if checks:
        drops = [
            (fear_1 - fear_2) / fear_1 if fear_1 else 0.0,
            (vol_1 - vol_2) / vol_1 if vol_1 else 0.0,
            (tr_1 - tr_2) / tr_1 if tr_1 else 0.0,
        ]
        score = max(0.0, min(100.0, 45 + max(drops) * 120 + (len(checks) - 1) * 10))
    return {
        "has_fear_cooling": bool(checks),
        "cooling_type": cooling_type,
        "fear_1": fear_1,
        "fear_2": fear_2,
        "volume_panic_1": vol_1,
        "volume_panic_2": vol_2,
        "volatility_fear_1": tr_1,
        "volatility_fear_2": tr_2,
        "cooling_score": float(score),
    }


def evaluate_min_support_context(
    frame: pd.DataFrame,
    body_zone_result: dict,
    trendline_result: dict,
    ma_context_result: dict,
    bollinger_result: dict,
    tolerance_pct: float = 0.7,
) -> dict:
    data = _normalize(frame)
    current = float(data.iloc[-1]["close"]) if not data.empty else 0.0
    sources: list[str] = []
    if body_zone_result.get("distance_to_support_pct", 999.0) <= tolerance_pct or body_zone_result.get("body_zone_score", 0.0) >= 30:
        sources.append("BODY_ZONE")
    if trendline_result.get("trendline_bounce") or abs(trendline_result.get("distance_to_trendline_pct", 999.0)) <= tolerance_pct:
        sources.append("TRENDLINE")
    recent_low = float(data["low"].tail(24).min()) if not data.empty else 0.0
    if current and recent_low and abs(current - recent_low) / current * 100 <= tolerance_pct:
        sources.append("PREVIOUS_LOW")
    ma30 = float(ma_context_result.get("ma30", 0.0))
    if current and ma30 and ma30 >= current and (ma30 - current) / current * 100 >= 0.25:
        sources.append("MA30_TARGET")
    middle = float(bollinger_result.get("middle_band", 0.0))
    target_space = body_zone_result.get("target_space_pct", 0.0)
    if current and middle and middle > current:
        target_space = max(float(target_space), (middle - current) / current * 100)
        if target_space >= 0.4:
            sources.append("BOLLINGER_MIDDLE_SPACE")
    score = min(100.0, len(set(sources)) * 25 + max(0.0, min(target_space, 2.0)) * 15)
    return {
        "has_min_support": bool(sources) and target_space >= 0.4,
        "support_sources": sorted(set(sources)),
        "support_context_score": float(score),
        "target_space_pct": float(target_space),
    }


def fallback_body_zone_context(frame: pd.DataFrame) -> dict:
    data = _normalize(frame)
    price = float(data.iloc[-1]["close"]) if not data.empty else 0.0
    return body_zone_context(data, price)


def _max(frame: pd.DataFrame, column: str) -> float:
    if column not in frame or frame.empty:
        return 0.0
    return float(frame[column].astype(float).max())


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)


def _empty_cooling() -> dict:
    return {
        "has_fear_cooling": False,
        "cooling_type": "NONE",
        "fear_1": 0.0,
        "fear_2": 0.0,
        "volume_panic_1": 0.0,
        "volume_panic_2": 0.0,
        "volatility_fear_1": 0.0,
        "volatility_fear_2": 0.0,
        "cooling_score": 0.0,
    }
