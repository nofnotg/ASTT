from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd

from adapters.upbit_client import UpbitClient, UpbitRateLimitError, UpbitTemporaryRateLimit
from app.config import get_settings
from replay_lab.data.data_quality import evaluate_candles
from replay_lab.lake.dataset_registry import DatasetRecord, DatasetRegistry
from replay_lab.lake.parquet_store import ParquetStore
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.settings import ReplaySettings


TIMEFRAME_UNITS = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


class HistoricalLoader:
    def __init__(
        self,
        client: UpbitClient | None = None,
        registry: DatasetRegistry | None = None,
        store: ParquetStore | None = None,
        settings: ReplaySettings | None = None,
        store_dir: Path | None = None,
    ) -> None:
        self.settings = settings or ReplaySettings()
        self.client = client or UpbitClient(get_settings(UPBIT_ACCESS_KEY="", UPBIT_SECRET_KEY=""))
        self.registry = registry or DatasetRegistry()
        self.store = store or ParquetStore()
        self.store_dir = store_dir or REPLAY_STORE_DIR

    def load_markets(self) -> list[str]:
        return self.client.get_krw_markets()

    def load_top_krw_markets(self, limit: int = 50) -> list[str]:
        markets = self.load_markets()
        ranked: list[str] = []
        for offset in range(0, len(markets), 100):
            tickers = self.client.get_ticker(markets[offset : offset + 100])
            ranked.extend(
                item["market"]
                for item in sorted(tickers, key=lambda row: row.get("acc_trade_price_24h", 0), reverse=True)
            )
        unique_ranked = []
        for market in ranked:
            if market not in unique_ranked:
                unique_ranked.append(market)
        return unique_ranked[:limit]

    def load_candles(self, market: str, timeframe: str, start: datetime, end: datetime) -> Path:
        start_s = start.isoformat()
        end_s = end.isoformat()
        cached = self.registry.find_covering(market, "candles", timeframe, start_s, end_s)
        if cached and Path(cached.storage_path).exists():
            return Path(cached.storage_path)

        frame = self._fetch_candles(market, timeframe, start, end)
        path = self.store_dir / "normalized" / f"candles_{timeframe}" / f"{market}.parquet"
        frame = self.store.append_dedup(frame, path, ["market", "timeframe", "candle_time_kst"])
        scoped = frame[(pd.to_datetime(frame["candle_time_kst"]) >= pd.Timestamp(start.replace(tzinfo=None))) & (pd.to_datetime(frame["candle_time_kst"]) <= pd.Timestamp(end.replace(tzinfo=None)))]
        quality = evaluate_candles(scoped)
        dataset_id = f"upbit_{market}_candles_{timeframe}_{start.date()}_{end.date()}"
        self.registry.upsert(
            DatasetRecord(
                dataset_id=dataset_id,
                exchange="upbit",
                market=market,
                data_type="candles",
                timeframe=timeframe,
                start_time_kst=start_s,
                end_time_kst=end_s,
                row_count=len(scoped),
                source="upbit_public_api",
                storage_path=str(path),
                quality_score=float(quality["quality_score"]),
                missing_count=int(quality["missing_count"]),
            )
        )
        return path

    def load_0900_window(self, market: str, day: date) -> Path:
        start = datetime.combine(day, time(0, 0))
        end = datetime.combine(day, time(10, 0))
        return self.load_candles(market, "1m", start, end)

    def load_0900_seconds_window(self, market: str, day: date) -> Path:
        start = datetime.combine(day, time(8, 50))
        end = datetime.combine(day, time(10, 0))
        return self.load_candles(market, "1s", start, end)

    def load_intraday_day(self, market: str, day: date) -> Path:
        start = datetime.combine(day, time(0, 0))
        end = datetime.combine(day, time(23, 59))
        return self.load_candles(market, "1m", start, end)

    def load_batch_0900_windows(self, markets: Iterable[str], start_date: date, end_date: date) -> list[Path]:
        paths = []
        day = start_date
        while day <= end_date:
            for market in markets:
                paths.append(self.load_0900_window(market, day))
            day += timedelta(days=1)
        return paths

    def load_batch_0900_seconds_windows(self, markets: Iterable[str], start_date: date, end_date: date) -> list[Path]:
        paths = []
        day = start_date
        while day <= end_date:
            for market in markets:
                paths.append(self.load_0900_seconds_window(market, day))
            day += timedelta(days=1)
        return paths

    def load_batch_intraday_days(self, markets: Iterable[str], start_date: date, end_date: date) -> list[Path]:
        paths = []
        day = start_date
        while day <= end_date:
            for market in markets:
                paths.append(self.load_intraday_day(market, day))
            day += timedelta(days=1)
        return paths

    def _fetch_candles(self, market: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        rows: list[dict] = []
        cursor = end
        while cursor >= start:
            batch = self._request_candles(market, timeframe, self._format_upbit_to(cursor))
            if not batch:
                break
            normalized = [self._normalize_candle(item, timeframe) for item in batch]
            rows.extend(normalized)
            oldest = min(pd.to_datetime(item["candle_time_kst"]).to_pydatetime() for item in normalized)
            if oldest <= start:
                break
            cursor = oldest - timedelta(minutes=1)
        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(columns=["market", "timeframe", "candle_time_kst", "open", "high", "low", "close", "volume", "trade_price"])
        frame["candle_time_kst"] = pd.to_datetime(frame["candle_time_kst"]).dt.tz_localize(None)
        frame = frame[(frame["candle_time_kst"] >= pd.Timestamp(start)) & (frame["candle_time_kst"] <= pd.Timestamp(end))]
        frame["candle_time_kst"] = frame["candle_time_kst"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return frame.sort_values("candle_time_kst")

    def _request_candles(self, market: str, timeframe: str, to_value: str) -> list[dict]:
        last_error: Exception | None = None
        for _ in range(self.settings.max_retry):
            try:
                if timeframe == "1d":
                    return self.client.get_candles_days(market, count=200, to=to_value)
                if timeframe == "1s":
                    return self.client.get_candles_seconds(market, count=200, to=to_value)
                unit = TIMEFRAME_UNITS[timeframe]
                return self.client.get_candles_minutes(market, unit=unit, count=200, to=to_value)
            except UpbitTemporaryRateLimit as exc:
                last_error = exc
                import time as time_module

                time_module.sleep(self.settings.backoff_seconds)
            except UpbitRateLimitError:
                raise
        if last_error:
            raise last_error
        return []

    def _normalize_candle(self, item: dict, timeframe: str) -> dict:
        return {
            "market": item["market"],
            "timeframe": timeframe,
            "candle_time_kst": item.get("candle_date_time_kst") or item.get("candle_time_kst"),
            "open": float(item.get("opening_price", item.get("open", 0))),
            "high": float(item.get("high_price", item.get("high", 0))),
            "low": float(item.get("low_price", item.get("low", 0))),
            "close": float(item.get("trade_price", item.get("close", 0))),
            "volume": float(item.get("candle_acc_trade_volume", item.get("volume", 0))),
            "trade_price": float(item.get("candle_acc_trade_price", item.get("trade_price", 0))),
        }

    def _format_upbit_to(self, value: datetime) -> str:
        # Upbit candle `to` is interpreted as UTC. Replay Lab works in KST.
        utc_value = value.replace(microsecond=0) - pd.Timedelta(hours=9)
        return utc_value.strftime("%Y-%m-%dT%H:%M:%S")

