from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from adapters.upbit_client import UpbitClient, UpbitRateLimitError, UpbitTemporaryRateLimit
from app.config import get_settings
from replay_lab.paths import REPLAY_STORE_DIR


MAX_SECOND_LOOKBACK_DAYS = 92


def fetch_second_candles(market: str, to=None, count: int = 200, unit: int = 1, client: UpbitClient | None = None) -> list[dict]:
    to_ts = pd.Timestamp(to or datetime.utcnow())
    if to_ts.tzinfo is not None:
        to_ts = to_ts.tz_convert(None)
    to_dt = to_ts.to_pydatetime()
    if datetime.utcnow() - to_dt > timedelta(days=MAX_SECOND_LOOKBACK_DAYS):
        return []
    client = client or UpbitClient(get_settings(UPBIT_ACCESS_KEY="", UPBIT_SECRET_KEY=""))
    last_error: Exception | None = None
    to_value = (to_dt - timedelta(hours=9)).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
    for attempt in range(3):
        try:
            return client.get_candles_seconds(market, count=count, to=to_value)
        except UpbitTemporaryRateLimit as exc:
            last_error = exc
            time.sleep(1.0 + attempt)
        except UpbitRateLimitError:
            raise
        except Exception as exc:  # network/API availability should not crash report generation
            last_error = exc
            time.sleep(0.5)
    if last_error:
        return []
    return []


def collect_second_candles(markets: list[str], days: int = 7, count_per_request: int = 200, store_dir: Path = REPLAY_STORE_DIR) -> dict:
    summary = {"requested_markets": markets, "requested_days": days, "available_days": 0, "actual_second_count": 0, "missing_second_count": 0, "data_quality": "UNAVAILABLE", "errors": []}
    now = datetime.utcnow() + timedelta(hours=9)
    for market in markets:
        rows: list[dict] = []
        for day_offset in range(days):
            to_dt = now - timedelta(days=day_offset)
            batch = fetch_second_candles(market, to=to_dt, count=count_per_request)
            rows.extend(_normalize(row) for row in batch)
        if rows:
            frame = pd.DataFrame(rows).drop_duplicates(subset=["candle_time_kst"]).sort_values("candle_time_kst")
            summary["actual_second_count"] += int(len(frame))
            summary["available_days"] += int(pd.to_datetime(frame["candle_time_kst"]).dt.date.nunique())
            _write_market_seconds(store_dir, market, frame)
    if summary["actual_second_count"] > 0:
        summary["data_quality"] = "PARTIAL" if summary["available_days"] < days * max(1, len(markets)) else "GOOD"
    return summary


def fill_missing_seconds(frame: pd.DataFrame, start_time, end_time) -> pd.DataFrame:
    start = pd.Timestamp(start_time)
    end = pd.Timestamp(end_time)
    all_seconds = pd.DataFrame({"time": pd.date_range(start, end, freq="s")})
    data = frame.copy()
    if data.empty:
        all_seconds["open"] = all_seconds["high"] = all_seconds["low"] = all_seconds["close"] = 0.0
        all_seconds["volume"] = 0.0
        all_seconds["synthetic"] = True
        return all_seconds
    data["time"] = pd.to_datetime(data.get("time", data.get("candle_time_kst")))
    merged = all_seconds.merge(data, on="time", how="left")
    merged["close"] = merged["close"].ffill().bfill().fillna(0.0)
    for col in ["open", "high", "low"]:
        merged[col] = merged[col].fillna(merged["close"])
    merged["volume"] = merged["volume"].fillna(0.0)
    merged["synthetic"] = merged["market"].isna() if "market" in merged else merged["volume"].eq(0)
    return merged[["time", "open", "high", "low", "close", "volume", "synthetic"]]


def _normalize(item: dict) -> dict:
    return {
        "market": item.get("market", ""),
        "candle_time_kst": item.get("candle_date_time_kst") or item.get("candle_time_kst"),
        "open": float(item.get("opening_price", item.get("open", 0.0))),
        "high": float(item.get("high_price", item.get("high", 0.0))),
        "low": float(item.get("low_price", item.get("low", 0.0))),
        "close": float(item.get("trade_price", item.get("close", 0.0))),
        "volume": float(item.get("candle_acc_trade_volume", item.get("volume", 0.0))),
        "trade_price": float(item.get("candle_acc_trade_price", item.get("trade_price", 0.0))),
    }


def _write_market_seconds(store_dir: Path, market: str, frame: pd.DataFrame) -> None:
    norm_root = store_dir / "normalized" / "upbit_seconds" / market
    raw_root = store_dir / "raw" / "upbit_seconds" / market
    norm_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)
    frame["date"] = pd.to_datetime(frame["candle_time_kst"]).dt.date.astype(str)
    for day, part in frame.groupby("date"):
        part.drop(columns=["date"]).to_parquet(norm_root / f"{day}.parquet", index=False)
        with (raw_root / f"{day}.jsonl").open("w", encoding="utf-8") as handle:
            for row in part.drop(columns=["date"]).to_dict("records"):
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
