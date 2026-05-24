from __future__ import annotations


def summarize_multi_timeframe_context(snapshot: dict) -> dict:
    price_change = float(snapshot.get("price_change_60s_pct", 0.0) or 0.0)
    state = "UP" if price_change > 0 else "FLAT_OR_DOWN"
    return {"1m_trend_state": state, "5m_trend_state": state, "15m_trend_state": state}
