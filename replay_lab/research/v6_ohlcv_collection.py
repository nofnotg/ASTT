from __future__ import annotations

from market_data.upbit_ohlcv_collector import collect_v6_ohlcv


def run_v6_ohlcv_collection(markets: str, months: int, timeframes: str) -> dict:
    return collect_v6_ohlcv(markets, months, timeframes)
