from __future__ import annotations

from adapters.upbit_client import UpbitClient
from data.storage import Storage


class MarketCollector:
    def __init__(self, client: UpbitClient, storage: Storage) -> None:
        self.client = client
        self.storage = storage

    def collect_minute_candles(self, market: str, unit: int = 1, count: int = 200) -> int:
        candles = self.client.get_candles_minutes(market, unit, count)
        return self.storage.upsert_candles(candles, timeframe=f"{unit}m")

    def top_krw_markets(self, limit: int = 50) -> list[str]:
        markets = self.client.get_krw_markets()
        tickers = self.client.get_ticker(markets[: min(len(markets), 100)])
        ranked = sorted(tickers, key=lambda item: item.get("acc_trade_price_24h", 0), reverse=True)
        return [item["market"] for item in ranked[:limit]]

