from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


class MarketRingBuffer:
    def __init__(self, window_seconds: int = 1800):
        self.window_seconds = max(600, int(window_seconds))
        self._rows: dict[str, deque[dict[str, Any]]] = defaultdict(deque)

    def append(self, market: str, row: dict[str, Any]) -> None:
        timestamp_ms = int(row.get("timestamp_ms") or row.get("trade_timestamp") or row.get("event_time_ms") or 0)
        item = {**row, "market": market, "timestamp_ms": timestamp_ms}
        bucket = self._rows[market]
        bucket.append(item)
        self._evict(market, timestamp_ms)

    def get_events(self, market: str, start_ms: int | None = None, end_ms: int | None = None, event_type: str | None = None) -> list[dict[str, Any]]:
        rows = list(self._rows.get(market, ()))
        if start_ms is not None:
            rows = [row for row in rows if int(row.get("timestamp_ms", 0)) >= start_ms]
        if end_ms is not None:
            rows = [row for row in rows if int(row.get("timestamp_ms", 0)) <= end_ms]
        if event_type is not None:
            rows = [row for row in rows if row.get("type") == event_type]
        return rows

    def extract_clip(self, market: str, center_ms: int, pre_seconds: int = 600, post_seconds: int = 1800) -> list[dict[str, Any]]:
        return self.get_events(market, center_ms - pre_seconds * 1000, center_ms + post_seconds * 1000)

    def markets(self) -> list[str]:
        return sorted(self._rows)

    def summary(self, market: str) -> dict[str, Any]:
        rows = self.get_events(market)
        counts = {"trade": 0, "orderbook": 0, "ticker": 0}
        for row in rows:
            kind = row.get("type")
            if kind in counts:
                counts[kind] += 1
        timestamps = [int(row.get("timestamp_ms", 0)) for row in rows if int(row.get("timestamp_ms", 0)) > 0]
        quality = "GOOD" if counts["trade"] and counts["orderbook"] else "PARTIAL" if rows else "POOR"
        return {
            "market": market,
            "buffer_window_seconds": self.window_seconds,
            "trade_event_count": counts["trade"],
            "orderbook_event_count": counts["orderbook"],
            "ticker_event_count": counts["ticker"],
            "start_time_ms": min(timestamps) if timestamps else 0,
            "end_time_ms": max(timestamps) if timestamps else 0,
            "quality": quality,
        }

    def _evict(self, market: str, newest_ms: int) -> None:
        cutoff = newest_ms - self.window_seconds * 1000
        bucket = self._rows[market]
        while bucket and int(bucket[0].get("timestamp_ms", 0)) < cutoff:
            bucket.popleft()
