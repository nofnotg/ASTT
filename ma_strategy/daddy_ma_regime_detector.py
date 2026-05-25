from __future__ import annotations

from typing import Any


def detect_daddy_ma_states(row: dict[str, Any]) -> list[str]:
    close = float(row.get("close", 0.0) or 0.0)
    sma20 = row.get("sma20")
    sma200 = row.get("sma200")
    slope200 = row.get("sma200_slope_pct")
    slope20 = row.get("sma20_slope_pct")
    if not close or sma20 is None or sma200 is None:
        return []

    states: list[str] = []
    gap_pct = abs(float(sma20) - float(sma200)) / close * 100.0
    distance_200 = (close / float(sma200) - 1.0) * 100.0 if sma200 else 0.0
    if close > float(sma200):
        states.append("MA_ABOVE_200")
    if close < float(sma200):
        states.append("MA_BELOW_200")
    if close > float(sma200) and (slope200 or 0.0) > 0 and (close >= float(sma20) or (slope20 or 0.0) > 0):
        states.append("MA_BULL")
    if close < float(sma200) and (slope200 or 0.0) < 0:
        states.append("MA_BEAR")
    if gap_pct <= 1.5:
        states.append("MA_SQUEEZE")
    if gap_pct <= 1.5 and close > float(sma20) > float(sma200) and (slope20 or 0.0) > 0:
        states.append("MA_SQUEEZE_BREAKOUT")
    if abs(slope200 or 0.0) < 0.03 or gap_pct <= 0.8:
        states.append("MA_CHOP")
    if distance_200 >= 25.0:
        states.append("MA_OVEREXTENDED")
    if close > float(sma20) and (slope20 or 0.0) > 0:
        states.append("MA_RECLAIM_20")
    if close < float(sma20):
        states.append("MA_LOST_20")
    return states
