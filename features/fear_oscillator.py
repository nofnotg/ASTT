from __future__ import annotations

import numpy as np
import pandas as pd


def compute_fear_oscillator(frame: pd.DataFrame, length: int = 30) -> pd.DataFrame:
    data = _normalize(frame)
    if data.empty:
        return data
    high_close = data["close"].rolling(length, min_periods=1).max()
    previous_close = data["close"].shift(1).fillna(data["close"])
    true_range = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(length, min_periods=1).mean().replace(0, np.nan)
    volume_mean = data["volume"].rolling(length, min_periods=1).mean().replace(0, np.nan)

    data["vix_fix"] = ((high_close - data["low"]) / high_close.replace(0, np.nan) * 100).fillna(0.0)
    data["volatility_fear"] = (true_range / atr).fillna(0.0)
    down_weight = (data["close"] < data["open"]).map({True: 1.25, False: 0.75})
    data["volume_panic"] = ((data["volume"] / volume_mean).fillna(0.0) * down_weight).clip(lower=0.0)
    data["fear_score"] = (
        _normalize_series(data["vix_fix"]) * 0.50
        + _normalize_series(data["volatility_fear"]) * 0.30
        + _normalize_series(data["volume_panic"]) * 0.20
    ).clip(0, 100)
    data["fear_zone"] = data["fear_score"].map(classify_fear_zone)
    return data


def latest_fear(frame: pd.DataFrame, length: int = 30) -> dict:
    data = compute_fear_oscillator(frame, length)
    if data.empty:
        return {"vix_fix": 0.0, "volatility_fear": 0.0, "volume_panic": 0.0, "fear_score": 0.0, "fear_zone": "NORMAL"}
    row = data.iloc[-1]
    return {
        "vix_fix": float(row["vix_fix"]),
        "volatility_fear": float(row["volatility_fear"]),
        "volume_panic": float(row["volume_panic"]),
        "fear_score": float(row["fear_score"]),
        "fear_zone": str(row["fear_zone"]),
    }


def classify_fear_zone(score: float) -> str:
    score = float(score)
    if score >= 85:
        return "EXTREME_PANIC"
    if score >= 70:
        return "PANIC"
    if score >= 45:
        return "FEAR"
    return "NORMAL"


def _normalize_series(series: pd.Series) -> pd.Series:
    low = float(series.rolling(120, min_periods=1).min().iloc[-1]) if len(series) else 0.0
    high = float(series.rolling(120, min_periods=1).max().iloc[-1]) if len(series) else 0.0
    if high <= low:
        return pd.Series(0.0, index=series.index)
    return ((series - low) / (high - low) * 100).fillna(0.0).clip(0, 100)


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    for column in ["open", "high", "low", "close", "volume"]:
        if column not in data:
            data[column] = 0.0
        data[column] = data[column].astype(float)
    return data.sort_values("time") if "time" in data else data
