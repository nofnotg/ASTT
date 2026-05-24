from __future__ import annotations

from typing import Any

from timing_lab.ring_buffer import MarketRingBuffer


class MarketRecorder:
    def __init__(self, buffer_minutes: int = 30):
        self.buffer = MarketRingBuffer(buffer_minutes * 60)

    def record(self, row: dict[str, Any]) -> None:
        market = row.get("market") or row.get("code") or row.get("raw", {}).get("code")
        if not market:
            return
        timestamp_ms = _timestamp_ms(row)
        kind = row.get("type") or row.get("raw", {}).get("type")
        normalized = {**row, "market": market, "timestamp_ms": timestamp_ms, "type": kind}
        self.buffer.append(market, normalized)

    def record_many(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            self.record(row)

    def summary(self) -> dict[str, Any]:
        markets = self.buffer.markets()
        summaries = [self.buffer.summary(market) for market in markets]
        return {
            "market_count": len(markets),
            "markets": markets,
            "buffers": summaries,
            "btc_included": "KRW-BTC" in markets,
            "quality": "GOOD" if any(item["quality"] == "GOOD" for item in summaries) else "PARTIAL" if summaries else "POOR",
            "real_order_enabled": False,
        }


def _timestamp_ms(row: dict[str, Any]) -> int:
    raw = row.get("raw", {}) if isinstance(row.get("raw"), dict) else {}
    return int(row.get("timestamp_ms") or row.get("trade_timestamp") or raw.get("trade_timestamp") or raw.get("timestamp") or 0)
