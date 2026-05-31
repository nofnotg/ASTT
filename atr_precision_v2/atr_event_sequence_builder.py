from __future__ import annotations

from typing import Any


def build_event_sequence(trade: dict[str, Any], bars: list[dict[str, Any]], exit_reason: str | None = None, exit_price: float | None = None) -> list[dict[str, Any]]:
    events = [{"event": "ENTRY", "time": trade.get("entry_time"), "price": trade.get("entry_price"), "market": trade.get("market")}]
    for bar in bars:
        events.append({"event": "BAR", "time": bar.get("timestamp"), "high": bar.get("high"), "low": bar.get("low"), "close": bar.get("close")})
    if exit_reason:
        events.append({"event": exit_reason, "time": bars[-1].get("timestamp") if bars else trade.get("exit_time"), "price": exit_price})
    return events
