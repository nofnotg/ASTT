from __future__ import annotations

import pandas as pd


def analyze_h4_structure(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 10:
        return {"h4_structure": "UNKNOWN", "score": 0.0}
    recent = frame.tail(12)
    high_break = float(recent["close"].iloc[-1]) >= float(recent["high"].iloc[:-1].max())
    low_break = float(recent["close"].iloc[-1]) <= float(recent["low"].iloc[:-1].min())
    if high_break:
        return {"h4_structure": "BREAKOUT", "score": 75.0}
    if low_break:
        return {"h4_structure": "BREAKDOWN", "score": 10.0}
    return {"h4_structure": "RANGE", "score": 45.0}
