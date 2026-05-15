from __future__ import annotations

import pandas as pd


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    if df is None or df.empty or len(df) < 2:
        return 0.0
    data = df.copy()
    prev_close = data["close"].shift(1)
    tr = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - prev_close).abs(),
            (data["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return float(tr.rolling(period, min_periods=1).mean().iloc[-1])

