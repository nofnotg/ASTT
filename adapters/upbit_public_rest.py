from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests

from adapters.upbit_rate_limiter import UpbitRateLimiter


BASE_URL = "https://api.upbit.com"


class UpbitPublicRest:
    def __init__(self, session: requests.Session | None = None, limiter: UpbitRateLimiter | None = None, timeout: int = 10) -> None:
        self.session = session or requests.Session()
        self.limiter = limiter or UpbitRateLimiter()
        self.timeout = timeout

    def get_second_candles(self, market: str, to: str | None = None, count: int = 200, unit: int = 1) -> list[dict]:
        if to and _older_than_roughly_three_months(to):
            return []
        params: dict[str, Any] = {"market": market, "count": count}
        if to:
            params["to"] = to
        last_error: Exception | None = None
        for attempt in range(3):
            self.limiter.wait()
            try:
                response = self.session.get(f"{BASE_URL}/v1/candles/seconds", params=params, timeout=self.timeout)
                if response.status_code == 429:
                    time.sleep(1.0 + attempt)
                    continue
                if response.status_code == 418:
                    return []
                response.raise_for_status()
                return [_normalize_second(row) for row in response.json()]
            except Exception as exc:
                last_error = exc
                time.sleep(0.5 + attempt * 0.5)
        if last_error:
            return []
        return []


def get_second_candles(market: str, to: str | None = None, count: int = 200, unit: int = 1) -> list[dict]:
    return UpbitPublicRest().get_second_candles(market, to=to, count=count, unit=unit)


def _normalize_second(row: dict) -> dict:
    return {
        "market": row.get("market", ""),
        "candle_date_time_utc": row.get("candle_date_time_utc"),
        "candle_date_time_kst": row.get("candle_date_time_kst"),
        "opening_price": float(row.get("opening_price", 0.0)),
        "high_price": float(row.get("high_price", 0.0)),
        "low_price": float(row.get("low_price", 0.0)),
        "trade_price": float(row.get("trade_price", 0.0)),
        "candle_acc_trade_volume": float(row.get("candle_acc_trade_volume", 0.0)),
        "candle_acc_trade_price": float(row.get("candle_acc_trade_price", 0.0)),
        "timestamp": int(row.get("timestamp", 0) or 0),
    }


def _older_than_roughly_three_months(to: str) -> bool:
    ts = pd.Timestamp(to)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return datetime.utcnow() - ts.to_pydatetime() > timedelta(days=93)
