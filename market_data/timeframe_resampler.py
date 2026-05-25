from __future__ import annotations

import pandas as pd

from market_data.ohlcv_store import empty_ohlcv, normalize_ohlcv


RESAMPLE_RULES = {
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
    "1w": "1W",
}


def resample_ohlcv(frame: pd.DataFrame, target_timeframe: str, market: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return empty_ohlcv()
    if target_timeframe == str(frame.get("timeframe", pd.Series([""])).iloc[0]):
        return normalize_ohlcv(frame, target_timeframe, market)
    rule = RESAMPLE_RULES[target_timeframe]
    data = normalize_ohlcv(frame, "1m", market).set_index("time")
    grouped = data.resample(rule, label="right", closed="right").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "trade_price": "sum",
        }
    )
    grouped = grouped.dropna(subset=["open", "high", "low", "close"]).reset_index()
    return normalize_ohlcv(grouped, target_timeframe, market)
