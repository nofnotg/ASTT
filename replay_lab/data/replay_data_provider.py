from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.paths import REPLAY_STORE_DIR


class ReplayDataProvider:
    def __init__(self, clock: ReplayClock, frames: dict[tuple[str, str], pd.DataFrame] | None = None, store_dir: Path | None = None) -> None:
        self.clock = clock
        self.frames = frames or {}
        self.store_dir = store_dir or REPLAY_STORE_DIR

    def get_markets(self) -> list[str]:
        markets = {market for market, _ in self.frames.keys()}
        if markets:
            return sorted(markets)
        candle_root = self.store_dir / "normalized" / "candles_1m"
        return sorted(path.stem for path in candle_root.glob("*.parquet")) if candle_root.exists() else []

    def get_candles(self, market: str, timeframe: str, count: int, to_time: datetime | None = None) -> pd.DataFrame:
        target_time = to_time or self.clock.current_time_kst
        self.clock.assert_not_future(target_time)
        frame = self._frame(market, timeframe)
        if frame.empty:
            return frame
        data = frame.copy()
        data["candle_time_kst"] = pd.to_datetime(data["candle_time_kst"])
        current = pd.Timestamp(target_time.replace(tzinfo=None))
        data = data[data["candle_time_kst"] <= current].sort_values("candle_time_kst").tail(count)
        for item in data["candle_time_kst"]:
            self.clock.assert_not_future(item.to_pydatetime())
        return data.rename(columns={"candle_time_kst": "time"})

    def get_ticker_snapshot(self, market: str, at_time: datetime) -> dict:
        candles = self.get_candles(market, "1m", 1, at_time)
        if candles.empty:
            return {"market": market, "trade_price": 0, "acc_trade_price_24h": 0}
        row = candles.iloc[-1]
        return {"market": market, "trade_price": float(row["close"]), "acc_trade_price_24h": float(row.get("trade_price", 0))}

    def get_orderbook_proxy(self, market: str, at_time: datetime) -> dict:
        ticker = self.get_ticker_snapshot(market, at_time)
        price = float(ticker["trade_price"])
        return {"market": market, "best_ask": price * 1.001, "best_bid": price * 0.999, "proxy": True}

    def get_trade_proxy(self, market: str, at_time: datetime) -> pd.DataFrame:
        candles = self.get_candles(market, "1m", 10, at_time)
        rows = []
        for _, row in candles.iterrows():
            rows.append({"ask_bid": "BID" if row["close"] >= row["open"] else "ASK", "trade_volume": float(row["volume"])})
        return pd.DataFrame(rows)

    def _frame(self, market: str, timeframe: str) -> pd.DataFrame:
        key = (market, timeframe)
        if key in self.frames:
            return self.frames[key].copy()
        path = self.store_dir / "normalized" / f"candles_{timeframe}" / f"{market}.parquet"
        if not path.exists():
            return pd.DataFrame(columns=["market", "timeframe", "candle_time_kst", "open", "high", "low", "close", "volume", "trade_price"])
        return pd.read_parquet(path)

