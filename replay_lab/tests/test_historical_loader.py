from datetime import datetime

from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.lake.dataset_registry import DatasetRegistry
from replay_lab.lake.parquet_store import ParquetStore


class FakeClient:
    def __init__(self):
        self.calls = 0

    def get_candles_minutes(self, market, unit, count=200, to=None):
        self.calls += 1
        return [
            {
                "market": market,
                "candle_date_time_kst": "2026-02-10T08:50:00",
                "opening_price": 100,
                "high_price": 101,
                "low_price": 99,
                "trade_price": 100,
                "candle_acc_trade_volume": 1,
                "candle_acc_trade_price": 100,
            }
        ]


def test_historical_loader_cache_hit(tmp_path):
    client = FakeClient()
    registry = DatasetRegistry(tmp_path / "manifest.sqlite")
    store = ParquetStore()
    loader = HistoricalLoader(client=client, registry=registry, store=store)
    start = datetime(2026, 2, 10, 8, 50)
    end = datetime(2026, 2, 10, 8, 50)
    first = loader.load_candles("KRW-BTC", "1m", start, end)
    second = loader.load_candles("KRW-BTC", "1m", start, end)
    assert first == second
    assert client.calls == 1

