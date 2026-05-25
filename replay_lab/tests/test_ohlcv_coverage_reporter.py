from __future__ import annotations

import pandas as pd

from market_data.ohlcv_coverage_reporter import build_ohlcv_coverage


def test_ohlcv_coverage_reporter_counts_timeframes(tmp_path):
    root = tmp_path / "ohlcv"
    path = root / "1d"
    path.mkdir(parents=True)
    pd.DataFrame({"time": pd.date_range("2024-01-01", periods=2), "open": [1, 2], "high": [1, 2], "low": [1, 2], "close": [1, 2], "volume": [1, 1]}).to_parquet(path / "KRW-BTC.parquet")
    summary = build_ohlcv_coverage(root, 36)
    assert summary["market_count"] == 1
    assert summary["candle_count_by_timeframe"]["1d"]["candles"] == 2
    assert summary["real_order_enabled"] is False
