from __future__ import annotations

from typing import Any


def detect_testa_states(row: dict[str, Any]) -> list[str]:
    close = float(row.get("close", 0.0) or 0.0)
    sma5 = row.get("sma5")
    sma25 = row.get("sma25")
    sma75 = row.get("sma75")
    slope5 = row.get("sma5_slope_pct") or 0.0
    slope25 = row.get("sma25_slope_pct") or 0.0
    slope75 = row.get("sma75_slope_pct") or 0.0
    if not close or sma5 is None or sma25 is None or sma75 is None:
        return []

    states: list[str] = []
    if float(sma5) > float(sma25) > float(sma75) and slope5 > 0 and slope25 > 0 and slope75 >= 0:
        states.append("TESTA_BULL_ALIGNMENT")
    if float(sma5) < float(sma25) < float(sma75) and slope5 < 0 and slope25 < 0:
        states.append("TESTA_BEAR_ALIGNMENT")
    if abs(float(sma5) - float(sma25)) / close * 100 < 0.6 and abs(float(sma25) - float(sma75)) / close * 100 < 1.2:
        states.append("TESTA_CHOP")
    if close < float(sma5) and close > float(sma25):
        states.append("TESTA_PULLBACK_BELOW_5")
    if close > float(sma5) and float(sma25) >= float(sma75):
        states.append("TESTA_RECLAIM_5")
    if abs(close - float(sma25)) / close * 100 <= 1.5:
        states.append("TESTA_SUPPORT_25")
    if close < float(sma75) and slope75 < 0:
        states.append("TESTA_LOST_75")
    if slope5 > 0.15 and slope25 > 0.08:
        states.append("TESTA_STRONG_SLOPE")
    if abs(slope25) < 0.03 and abs(slope75) < 0.03:
        states.append("TESTA_WEAK_SLOPE")
    return states
