from __future__ import annotations


def plan_high_volatility_session(session_type: str, duration_minutes: int = 60, top_markets: int = 30) -> dict:
    windows = {
        "MORNING_0900": "08:50-09:40 KST",
        "US_OPEN_2230": "22:20-23:20 KST",
        "BTC_SHOCK": "triggered by BTC 1m abs move",
        "VOLUME_SPIKE_MARKET": "triggered by KRW volume rank change",
        "RANDOM_CONTROL": "any ordinary period",
    }
    return {
        "session_type": session_type,
        "recommended_window": windows.get(session_type, "manual"),
        "duration_minutes": duration_minutes,
        "top_markets": top_markets,
        "markets_include_btc": True,
        "real_order_enabled": False,
    }
