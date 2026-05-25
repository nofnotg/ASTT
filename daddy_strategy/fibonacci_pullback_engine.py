from __future__ import annotations

import pandas as pd


def detect_fibonacci_pullback(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 30:
        return {"fib_state": "UNKNOWN", "score": 0.0}
    recent = frame.tail(60)
    swing_low = float(recent["low"].min())
    swing_high = float(recent["high"].max())
    close = float(recent["close"].iloc[-1])
    span = max(swing_high - swing_low, 1e-9)
    fib50 = swing_high - span * 0.5
    fib618 = swing_high - span * 0.618
    near = min(abs(close - fib50), abs(close - fib618)) / max(close, 1e-9) * 100
    if near <= 1.2:
        return {"fib_state": "FIB_REACTION_ZONE", "fib_50": fib50, "fib_618": fib618, "score": 72.0}
    return {"fib_state": "OUTSIDE_FIB_ZONE", "fib_50": fib50, "fib_618": fib618, "score": 25.0}
