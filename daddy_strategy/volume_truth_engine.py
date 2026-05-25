from __future__ import annotations

import pandas as pd


def analyze_volume_truth(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 20:
        return {"volume_signal": "INSUFFICIENT", "volume_ratio": 0.0, "score": 0.0}
    recent = frame.tail(20)
    close = recent["close"].astype(float)
    high = recent["high"].astype(float)
    low = recent["low"].astype(float)
    volume = recent["volume"].astype(float)
    volume_ratio = float(volume.iloc[-1] / max(volume.mean(), 1e-9))
    breakout = close.iloc[-1] > high.iloc[:-1].max()
    lower_wick = (min(close.iloc[-1], recent["open"].iloc[-1]) - low.iloc[-1]) / max(close.iloc[-1], 1e-9) * 100
    if breakout and volume_ratio >= 1.3:
        signal, score = "BREAKOUT_WITH_VOLUME", 80.0
    elif breakout:
        signal, score = "BREAKOUT_WITHOUT_VOLUME", 45.0
    elif close.iloc[-1] > close.iloc[-5] and volume.iloc[-1] < volume.tail(5).mean():
        signal, score = "PRICE_UP_VOLUME_DOWN", 30.0
    elif lower_wick >= 0.4 and volume_ratio >= 1.2:
        signal, score = "PULLBACK_WICK_VOLUME", 70.0
    elif volume_ratio >= 1.5 and close.iloc[-1] <= close.iloc[-5]:
        signal, score = "BOTTOM_VOLUME", 65.0
    else:
        signal, score = "NEUTRAL", 35.0
    return {"volume_signal": signal, "volume_ratio": volume_ratio, "score": score}
