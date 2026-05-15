from __future__ import annotations

import pandas as pd


def moving_average_context(frame: pd.DataFrame) -> dict:
    data = _normalize(frame)
    if data.empty:
        return _empty_ma()
    close = data["close"].astype(float)
    current = float(close.iloc[-1])
    ma20 = float(close.rolling(20, min_periods=1).mean().iloc[-1])
    ma30 = float(close.rolling(30, min_periods=1).mean().iloc[-1])
    ma60 = float(close.rolling(60, min_periods=1).mean().iloc[-1])
    ma224 = float(close.rolling(224, min_periods=1).mean().iloc[-1])
    score = 35.0
    if current >= ma30:
        score += 25
    if current >= ma20 and current >= ma30:
        score += 15
    if current >= ma60:
        score += 10
    score += 15 if current >= ma224 else -10
    return {
        "ma20": ma20,
        "ma30": ma30,
        "ma60": ma60,
        "ma224": ma224,
        "ma_context_score": max(0.0, min(100.0, score)),
        "first_take_profit": "middle_band_or_ma30",
    }


def body_zone_context(frame: pd.DataFrame, price: float | None = None, volume_quantile: float = 0.8) -> dict:
    data = _normalize(frame)
    if data.empty:
        return _empty_zone()
    current = float(price if price is not None else data.iloc[-1]["close"])
    threshold = float(data["volume"].astype(float).quantile(volume_quantile))
    heavy = data[data["volume"].astype(float) >= threshold].copy()
    if heavy.empty:
        return _empty_zone()
    heavy["body_low"] = heavy[["open", "close"]].astype(float).min(axis=1)
    heavy["body_high"] = heavy[["open", "close"]].astype(float).max(axis=1)
    supports = heavy[heavy["body_low"] <= current]
    resistances = heavy[heavy["body_high"] > current]
    support = supports.iloc[(current - supports["body_high"]).abs().argsort().iloc[0]] if not supports.empty else None
    resistance = resistances.iloc[(resistances["body_low"] - current).abs().argsort().iloc[0]] if not resistances.empty else None
    support_zone = [float(support["body_low"]), float(support["body_high"])] if support is not None else [0.0, 0.0]
    resistance_zone = [float(resistance["body_low"]), float(resistance["body_high"])] if resistance is not None else [0.0, 0.0]
    distance = _distance_to_zone_pct(current, support_zone)
    target_space = ((resistance_zone[0] - current) / current * 100) if current and resistance_zone[0] else 999.0
    score = 0.0
    if distance <= 0.5:
        score += 55
    elif distance <= 1.0:
        score += 40
    elif distance <= 2.0:
        score += 25
    if target_space >= 1.2:
        score += 25
    elif target_space < 0.6:
        score -= 20
    return {
        "nearest_support_zone": support_zone,
        "distance_to_support_pct": float(distance),
        "nearest_resistance_zone": resistance_zone,
        "target_space_pct": float(target_space),
        "body_zone_score": max(0.0, min(100.0, score)),
    }


def _distance_to_zone_pct(price: float, zone: list[float]) -> float:
    if not price or not zone or zone == [0.0, 0.0]:
        return 999.0
    low, high = zone
    if low <= price <= high:
        return 0.0
    anchor = high if price > high else low
    return abs(price - anchor) / price * 100 if price else 999.0


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)


def _empty_ma() -> dict:
    return {"ma20": 0.0, "ma30": 0.0, "ma60": 0.0, "ma224": 0.0, "ma_context_score": 0.0, "first_take_profit": "middle_band_or_ma30"}


def _empty_zone() -> dict:
    return {"nearest_support_zone": [0.0, 0.0], "distance_to_support_pct": 999.0, "nearest_resistance_zone": [0.0, 0.0], "target_space_pct": 0.0, "body_zone_score": 0.0}
