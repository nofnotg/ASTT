from __future__ import annotations

import pandas as pd


def compute_bollinger(frame: pd.DataFrame, length: int = 30, stddev: float = 2.0) -> pd.DataFrame:
    data = _normalize(frame)
    if data.empty:
        return data
    middle = data["close"].astype(float).rolling(length, min_periods=length).mean()
    deviation = data["close"].astype(float).rolling(length, min_periods=length).std(ddof=0)
    data["middle_band"] = middle
    data["upper_band"] = middle + deviation * stddev
    data["lower_band"] = middle - deviation * stddev
    return data


def detect_lower_band_reentry(frame: pd.DataFrame, length: int = 30, stddev: float = 2.0, lookback: int = 3) -> dict:
    data = compute_bollinger(frame, length, stddev)
    if data.empty or len(data) < length + 1:
        return _empty()
    recent = data.tail(max(2, lookback + 1))
    current = recent.iloc[-1]
    previous = recent.iloc[:-1]
    lower = float(current.get("lower_band", 0.0) or 0.0)
    middle = float(current.get("middle_band", 0.0) or 0.0)
    upper = float(current.get("upper_band", 0.0) or 0.0)
    had_break = bool((previous["low"].astype(float) < previous["lower_band"].astype(float)).any())
    reentered = bool(had_break and float(current["close"]) > lower and float(current["low"]) <= lower * 1.01)
    candle_range = float(current["high"]) - float(current["low"])
    close_position = (float(current["close"]) - float(current["low"])) / candle_range if candle_range else 0.0
    reentry_strength = max(0.0, min(100.0, close_position * 60 + (float(current["close"]) - lower) / lower * 1000 if lower else 0.0)) if reentered else 0.0
    return {
        "lower_band": lower,
        "middle_band": middle,
        "upper_band": upper,
        "reentered_lower_band": reentered,
        "reentry_strength": float(reentry_strength),
    }


def _empty() -> dict:
    return {"lower_band": 0.0, "middle_band": 0.0, "upper_band": 0.0, "reentered_lower_band": False, "reentry_strength": 0.0}


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
