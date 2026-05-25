from __future__ import annotations

import pandas as pd


def analyze_weekly_trend(frame: pd.DataFrame) -> dict:
    return _trend(frame, "weekly_trend")


def _trend(frame: pd.DataFrame, key: str) -> dict:
    if frame is None or len(frame) < 3:
        return {key: "UNKNOWN", "score": 0.0}
    close = frame["close"].astype(float)
    ma = close.rolling(min(20, max(2, len(close) // 2))).mean()
    slope = close.iloc[-1] - close.iloc[max(0, len(close) - 4)]
    trend = "UP" if close.iloc[-1] >= ma.iloc[-1] and slope >= 0 else "DOWN" if close.iloc[-1] < ma.iloc[-1] and slope < 0 else "CHOP"
    return {key: trend, "score": 70.0 if trend == "UP" else 35.0 if trend == "CHOP" else 15.0}
