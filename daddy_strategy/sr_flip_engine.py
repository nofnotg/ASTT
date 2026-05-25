from __future__ import annotations

import pandas as pd


def detect_sr_flip(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 30:
        return {"sr_flip_state": "UNKNOWN", "level": 0.0, "score": 0.0}
    recent = frame.tail(40)
    resistance = float(recent["high"].iloc[:-3].max())
    close = float(recent["close"].iloc[-1])
    low = float(recent["low"].iloc[-1])
    if low <= resistance <= close:
        return {"sr_flip_state": "RETEST_HOLD", "level": resistance, "score": 78.0}
    if close > resistance:
        return {"sr_flip_state": "BREAKOUT", "level": resistance, "score": 62.0}
    return {"sr_flip_state": "NO_FLIP", "level": resistance, "score": 25.0}
