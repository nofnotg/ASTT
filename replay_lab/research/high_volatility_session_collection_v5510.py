from __future__ import annotations

from live_capture.upbit_live_ws_collector_v5510 import collect_high_volatility_live_session_v5510


def collect_high_volatility_session_v5510(session_type: str, duration_minutes: int, top_markets: int) -> dict:
    return collect_high_volatility_live_session_v5510(session_type, duration_minutes, top_markets)
