from __future__ import annotations

import pandas as pd


def analyze_ma20(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 20:
        return {"ma20_state": "UNKNOWN", "ma20": 0.0, "score": 0.0}
    close = frame["close"].astype(float)
    ma20 = close.rolling(20).mean().iloc[-1]
    prev = close.iloc[-2]
    now = close.iloc[-1]
    if now > ma20 and prev <= ma20:
        state, score = "MA20_RECLAIM", 80.0
    elif now > ma20:
        state, score = "ABOVE_MA20", 65.0
    else:
        state, score = "BELOW_MA20", 20.0
    return {"ma20_state": state, "ma20": float(ma20), "score": score}
