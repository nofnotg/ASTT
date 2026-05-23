from __future__ import annotations

import pandas as pd


def check_live_micro_health(session_id: str, trades, orderbooks, stale_seconds: float = 10.0) -> dict:
    trade_frame = pd.DataFrame(trades or [])
    ob_frame = pd.DataFrame(orderbooks or [])
    markets = sorted(set(trade_frame.get("market", pd.Series(dtype=str))).union(set(ob_frame.get("market", pd.Series(dtype=str)))))
    result = {"session_id": session_id, "healthy": True, "markets": {}, "warnings": []}
    now_ms = max([0] + trade_frame.get("received_at_ms", pd.Series(dtype=float)).tolist() + ob_frame.get("received_at_ms", pd.Series(dtype=float)).tolist())
    for market in markets:
        t = trade_frame[trade_frame["market"] == market] if not trade_frame.empty and "market" in trade_frame else pd.DataFrame()
        o = ob_frame[ob_frame["market"] == market] if not ob_frame.empty and "market" in ob_frame else pd.DataFrame()
        last_t = float(t["received_at_ms"].max()) if not t.empty and "received_at_ms" in t else 0.0
        last_o = float(o["received_at_ms"].max()) if not o.empty and "received_at_ms" in o else 0.0
        quality = "GOOD" if len(t) and len(o) else ("PARTIAL" if len(t) or len(o) else "UNAVAILABLE")
        if quality != "GOOD":
            result["healthy"] = False
            result["warnings"].append(f"{market}_quality_{quality.lower()}")
        result["markets"][market] = {"trade_events": int(len(t)), "orderbook_events": int(len(o)), "last_trade_age_sec": max(0.0, (now_ms - last_t) / 1000), "last_orderbook_age_sec": max(0.0, (now_ms - last_o) / 1000), "data_quality": quality}
    return result
