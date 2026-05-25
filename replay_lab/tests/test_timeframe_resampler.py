import pandas as pd

from market_data.timeframe_resampler import resample_ohlcv


def test_timeframe_resampler_builds_5m_candle():
    frame = pd.DataFrame([{"time": f"2026-01-01T00:0{i}:00", "open": 100 + i, "high": 101 + i, "low": 99 + i, "close": 100 + i, "volume": 1, "trade_price": 100} for i in range(5)])
    out = resample_ohlcv(frame, "5m", "KRW-BTC")
    assert len(out) >= 1
    assert out.iloc[-1]["market"] == "KRW-BTC"
