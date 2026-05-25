from __future__ import annotations

import pandas as pd


def detect_neckline(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 30:
        return {"neckline": 0.0, "neckline_state": "UNKNOWN", "score": 0.0}
    recent = frame.tail(40)
    highs = recent["high"].astype(float)
    neckline = float(highs.quantile(0.85))
    close = float(recent["close"].iloc[-1])
    distance = abs(close - neckline) / max(close, 1e-9) * 100
    if close > neckline and distance <= 2.0:
        state, score = "BREAKOUT_RETEST_AREA", 75.0
    elif distance <= 1.5:
        state, score = "NEAR_NECKLINE", 60.0
    else:
        state, score = "FAR_FROM_NECKLINE", 25.0
    return {"neckline": neckline, "neckline_state": state, "distance_pct": distance, "score": score}
