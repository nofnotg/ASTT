from __future__ import annotations

from live_data.upbit_real_ws_session import run_upbit_real_ws_session


def run_upbit_ws_smoke_test(markets: list[str], duration_seconds: int = 300) -> dict:
    result = run_upbit_real_ws_session(markets, duration_seconds=duration_seconds, include_trade=True, include_orderbook=True)
    result["success"] = result.get("trade_event_count", 0) > 0 and result.get("orderbook_event_count", 0) > 0
    return result
