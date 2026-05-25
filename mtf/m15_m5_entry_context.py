from __future__ import annotations

import pandas as pd


def lower_timeframe_confirmation(m15: pd.DataFrame, m5: pd.DataFrame) -> dict:
    frames = [frame for frame in [m15, m5] if frame is not None and len(frame) >= 3]
    if not frames:
        return {"confirmed": False, "score": 0.0}
    score = 0.0
    for frame in frames:
        score += 25.0 if float(frame["close"].iloc[-1]) >= float(frame["open"].iloc[-1]) else 0.0
    return {"confirmed": score >= 25.0, "score": score}
