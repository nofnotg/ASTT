from __future__ import annotations


def evaluate_live_session_quality(trade_event_count: int, orderbook_event_count: int, ticker_event_count: int = 0, duration_minutes: int = 0) -> dict:
    expected_floor = max(10, duration_minutes * 5)
    warnings = []
    if trade_event_count < expected_floor:
        warnings.append("TRADE_EVENT_COUNT_LOW")
    if orderbook_event_count < expected_floor:
        warnings.append("ORDERBOOK_EVENT_COUNT_LOW")
    if ticker_event_count <= 0:
        warnings.append("TICKER_EVENT_COUNT_LOW")
    if trade_event_count >= expected_floor and orderbook_event_count >= expected_floor:
        quality = "GOOD" if ticker_event_count > 0 else "PARTIAL"
    elif trade_event_count or orderbook_event_count:
        quality = "PARTIAL"
    else:
        quality = "POOR"
    return {"quality": quality, "warnings": warnings}
