import pandas as pd

from market_data.ohlcv_store import OHLCVStore
from market_data.upbit_ohlcv_collector import collect_v6_ohlcv


def test_collect_v6_ohlcv_uses_local_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "replay_store" / "normalized" / "candles_1m"
    source.mkdir(parents=True)
    times = pd.date_range("2026-05-25T00:00:00", periods=5, freq="min")
    pd.DataFrame(
        [{"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": str(time), "open": 100, "high": 101, "low": 99, "close": 100 + i, "volume": 1, "trade_price": 100} for i, time in enumerate(times)]
    ).to_parquet(source / "KRW-BTC.parquet", index=False)
    import market_data.upbit_ohlcv_collector as mod

    monkeypatch.setattr(mod, "REPLAY_STORE_DIR", tmp_path / "replay_store")
    result = collect_v6_ohlcv("KRW-BTC", 12, "1m,5m", OHLCVStore(tmp_path / "v6"))
    assert result["by_timeframe"]["1m"]["candles"] == 5
    assert result["real_order_enabled"] is False
