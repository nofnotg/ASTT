from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any

KST = timezone(timedelta(hours=9))


def typical_price(row: dict[str, Any]) -> float:
    high = float(row.get("high", row.get("price", row.get("close", 0.0))) or 0.0)
    low = float(row.get("low", row.get("price", row.get("close", 0.0))) or 0.0)
    close = float(row.get("close", row.get("price", 0.0)) or 0.0)
    return (high + low + close) / 3.0 if high or low or close else 0.0


def volume(row: dict[str, Any]) -> float:
    return float(row.get("volume", row.get("candle_acc_trade_volume", 0.0)) or 0.0)


def parse_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def daily_anchor_key(row: dict[str, Any]) -> str:
    ts = parse_time(row.get("timestamp") or row.get("time") or row.get("date"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=KST)
    kst = ts.astimezone(KST)
    if kst.hour < 9:
        kst = kst - timedelta(days=1)
    return kst.date().isoformat()


def rolling_vwap(rows: list[dict[str, Any]], window: int) -> list[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    pv_queue: deque[float] = deque()
    vol_queue: deque[float] = deque()
    pv_sum = 0.0
    vol_sum = 0.0
    out: list[float] = []
    for row in rows:
        vol = volume(row)
        pv = typical_price(row) * vol
        pv_queue.append(pv)
        vol_queue.append(vol)
        pv_sum += pv
        vol_sum += vol
        if len(pv_queue) > window:
            pv_sum -= pv_queue.popleft()
            vol_sum -= vol_queue.popleft()
        out.append(pv_sum / vol_sum if vol_sum else 0.0)
    return out


def daily_anchored_vwap(rows: list[dict[str, Any]]) -> list[float]:
    out: list[float] = []
    current_key: str | None = None
    pv_sum = 0.0
    vol_sum = 0.0
    for row in rows:
        key = daily_anchor_key(row)
        if key != current_key:
            current_key = key
            pv_sum = 0.0
            vol_sum = 0.0
        vol = volume(row)
        pv_sum += typical_price(row) * vol
        vol_sum += vol
        out.append(pv_sum / vol_sum if vol_sum else 0.0)
    return out


def attach_vwap_features(rows: list[dict[str, Any]], rolling_4h: int = 4, rolling_24h: int = 24) -> list[dict[str, Any]]:
    daily = daily_anchored_vwap(rows)
    vw4 = rolling_vwap(rows, rolling_4h)
    vw24 = rolling_vwap(rows, rolling_24h)
    enriched = []
    for idx, row in enumerate(rows):
        close = float(row.get("close", row.get("price", 0.0)) or 0.0)
        vwap = daily[idx]
        distance = ((close / vwap) - 1.0) * 100.0 if vwap else 0.0
        enriched.append(
            {
                **row,
                "daily_anchored_vwap": vwap,
                "rolling_vwap_4h": vw4[idx],
                "rolling_vwap_24h": vw24[idx],
                "price_above_vwap": close > vwap,
                "price_below_vwap": close < vwap,
                "vwap_distance_pct": distance,
            }
        )
    return enriched
