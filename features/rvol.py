from __future__ import annotations

import pandas as pd


def calculate_rvol(df: pd.DataFrame, lookback: int = 20) -> dict:
    if df is None or df.empty:
        return {"rvol": 0.0, "volume_acceleration": 0.0, "trade_amount_acceleration": 0.0, "warning": "insufficient candle data"}
    data = df.copy()
    avg_volume = float(data["volume"].tail(lookback).mean() or 0)
    current_volume = float(data["volume"].iloc[-1])
    prev_volume = float(data["volume"].iloc[-2]) if len(data) > 1 else current_volume
    rvol = current_volume / avg_volume if avg_volume else 0.0
    volume_acceleration = current_volume / prev_volume if prev_volume else 0.0
    data["trade_amount"] = data["close"] * data["volume"]
    current_amount = float(data["trade_amount"].iloc[-1])
    prev_amount = float(data["trade_amount"].iloc[-2]) if len(data) > 1 else current_amount
    return {
        "rvol": rvol,
        "volume_acceleration": volume_acceleration,
        "trade_amount_acceleration": current_amount / prev_amount if prev_amount else 0.0,
    }

