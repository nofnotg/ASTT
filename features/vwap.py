from __future__ import annotations

import pandas as pd


def calculate_vwap(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"vwap": 0.0, "above_vwap": False, "warning": "insufficient candle data"}
    data = df.copy()
    typical = (data["high"] + data["low"] + data["close"]) / 3
    volume = data["volume"].replace(0, pd.NA)
    vwap = float((typical * data["volume"]).sum() / volume.sum()) if volume.sum() else 0.0
    current = float(data["close"].iloc[-1])
    return {"vwap": vwap, "current_price": current, "above_vwap": current >= vwap if vwap else False}


def calculate_session_vwap(df: pd.DataFrame, since_time: str = "09:00") -> dict:
    if "time" not in df.columns:
        return calculate_vwap(df)
    session = df[df["time"].astype(str).str[-8:] >= since_time + ":00"]
    return calculate_vwap(session if not session.empty else df.tail(1))

