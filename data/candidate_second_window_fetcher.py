from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pandas as pd

from adapters.upbit_public_rest import get_second_candles
from data.candidate_second_window_store import store_candidate_second_window
from data.second_window_quality import evaluate_second_window_quality


def fetch_candidate_second_window(market: str, candidate_time, pre_seconds: int = 120, post_seconds: int = 180, unit: int = 1, max_requests: int = 3) -> dict:
    candidate_ts = pd.Timestamp(candidate_time)
    if candidate_ts.tzinfo is not None:
        candidate_ts = candidate_ts.tz_convert("Asia/Seoul").tz_localize(None)
    start = candidate_ts - pd.Timedelta(seconds=pre_seconds)
    end = candidate_ts + pd.Timedelta(seconds=post_seconds)
    rows = []
    warnings = []
    # Upbit candle API returns reverse chronological candles before "to"; fetch around end of window.
    to_value = (end - pd.Timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S")
    for _ in range(max_requests):
        batch = get_second_candles(market, to=to_value, count=200, unit=unit)
        if not batch:
            break
        rows.extend(batch)
        oldest = min(pd.Timestamp(item["candle_date_time_kst"]) for item in batch if item.get("candle_date_time_kst"))
        if oldest <= start:
            break
        to_value = (oldest - pd.Timedelta(seconds=1) - pd.Timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S")
    seconds = _fill_window(rows, start, end)
    window = {"candidate_id": f"cand_{uuid4().hex[:12]}", "market": market, "candidate_time": candidate_ts.isoformat(), "window_start": start.isoformat(), "window_end": end.isoformat(), "pre_seconds": pre_seconds, "post_seconds": post_seconds, "actual_second_count": int(sum(not row["synthetic"] for row in seconds)), "missing_second_count": int(sum(row["synthetic"] for row in seconds)), "synthetic_second_count": int(sum(row["synthetic"] for row in seconds)), "data_quality": "UNAVAILABLE", "seconds": seconds, "warnings": warnings, "data_source": "UPBIT_REST_SECONDS"}
    quality = evaluate_second_window_quality(window)
    window["data_quality"] = quality["quality_grade"]
    window["quality"] = quality
    window["warnings"].extend(quality["warnings"])
    paths = store_candidate_second_window(window)
    window["storage"] = paths
    return window


def _fill_window(rows: list[dict], start: pd.Timestamp, end: pd.Timestamp) -> list[dict]:
    by_time = {}
    for row in rows:
        ts = pd.Timestamp(row.get("candle_date_time_kst"))
        if start <= ts <= end:
            by_time[ts.floor("s")] = row
    out = []
    last_price = None
    for ts in pd.date_range(start, end, freq="s"):
        row = by_time.get(ts)
        if row:
            price = float(row.get("trade_price", 0.0))
            last_price = price
            out.append({"time": ts.isoformat(), "open": float(row.get("opening_price", price)), "high": float(row.get("high_price", price)), "low": float(row.get("low_price", price)), "close": price, "volume": float(row.get("candle_acc_trade_volume", 0.0)), "synthetic": False})
        else:
            price = last_price or 0.0
            out.append({"time": ts.isoformat(), "open": price, "high": price, "low": price, "close": price, "volume": 0.0, "synthetic": True})
    return out
