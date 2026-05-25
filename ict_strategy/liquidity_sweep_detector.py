from __future__ import annotations

import pandas as pd


def detect_liquidity_sweeps(frame: pd.DataFrame) -> list[dict]:
    if frame is None or len(frame) < 20:
        return []
    data = frame.reset_index(drop=True)
    sweeps = []
    for idx in range(10, len(data)):
        prev_low = float(data.iloc[idx - 10 : idx]["low"].min())
        prev_high = float(data.iloc[idx - 10 : idx]["high"].max())
        row = data.iloc[idx]
        close = float(row["close"])
        if float(row["low"]) < prev_low and close > prev_low:
            sweeps.append({"sweep_type": "BULLISH_LIQUIDITY_SWEEP", "swept_level": prev_low, "reclaim_price": close, "reclaim_time": str(row["time"]), "quality_score": 72.0})
        if float(row["high"]) > prev_high and close < prev_high:
            sweeps.append({"sweep_type": "BEARISH_LIQUIDITY_SWEEP", "swept_level": prev_high, "reclaim_price": close, "reclaim_time": str(row["time"]), "quality_score": 45.0})
    return sweeps[-10:]
