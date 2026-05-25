from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


class OHLCVStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else REPLAY_STORE_DIR / "v6_ohlcv"

    def path(self, timeframe: str, market: str) -> Path:
        return self.root / timeframe / f"{market}.parquet"

    def save(self, timeframe: str, market: str, frame: pd.DataFrame) -> Path:
        path = self.path(timeframe, market)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize_ohlcv(frame, timeframe, market)
        normalized.to_parquet(path, index=False)
        return path

    def load(self, timeframe: str, market: str) -> pd.DataFrame:
        path = self.path(timeframe, market)
        if not path.exists():
            return empty_ohlcv()
        return normalize_ohlcv(pd.read_parquet(path), timeframe, market)

    def list_markets(self, timeframe: str = "1d") -> list[str]:
        root = self.root / timeframe
        return sorted(path.stem for path in root.glob("*.parquet")) if root.exists() else []

    def write_summary(self, payload: dict[str, Any]) -> None:
        path = self.root / "latest_v6_ohlcv_summary.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def empty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(columns=["market", "timeframe", "time", "open", "high", "low", "close", "volume", "trade_price"])


def normalize_ohlcv(frame: pd.DataFrame, timeframe: str, market: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return empty_ohlcv()
    data = frame.copy()
    if "time" not in data.columns:
        if "candle_time_kst" in data.columns:
            data["time"] = data["candle_time_kst"]
        elif "timestamp" in data.columns:
            data["time"] = data["timestamp"]
    for column in ["open", "high", "low", "close", "volume"]:
        if column not in data.columns:
            data[column] = 0.0
    if "trade_price" not in data.columns:
        data["trade_price"] = data["close"] * data["volume"]
    data["time"] = pd.to_datetime(data["time"]).dt.tz_localize(None)
    data["market"] = market
    data["timeframe"] = timeframe
    data = data[["market", "timeframe", "time", "open", "high", "low", "close", "volume", "trade_price"]]
    return data.drop_duplicates(subset=["market", "timeframe", "time"]).sort_values("time").reset_index(drop=True)
