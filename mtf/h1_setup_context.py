from __future__ import annotations

import pandas as pd


def analyze_h1_setup_context(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 20:
        return {"h1_setup_bias": "UNKNOWN", "score": 0.0}
    close = frame["close"].astype(float)
    volume = frame["volume"].astype(float)
    ma20 = close.rolling(20).mean()
    vol_ratio = volume.iloc[-1] / max(volume.tail(20).mean(), 1e-9)
    if close.iloc[-1] > ma20.iloc[-1] and vol_ratio >= 1.2:
        return {"h1_setup_bias": "LONG_SETUP", "score": 75.0}
    if close.iloc[-1] > ma20.iloc[-1]:
        return {"h1_setup_bias": "LONG_WATCH", "score": 55.0}
    return {"h1_setup_bias": "NO_LONG", "score": 20.0}
