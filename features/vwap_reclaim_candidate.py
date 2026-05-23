from __future__ import annotations

from features.micro_candidate_sources import _candidate


def detect_vwap_reclaim_candidate(market: str, snapshot: dict, minute_context: dict, config: dict | None = None) -> dict | None:
    cfg = {"buy_trade_ratio_5s": 0.52, "spread_pct": 0.20, **(config or {})}
    vwap = float(minute_context.get("vwap", 0.0))
    price = float(snapshot.get("last_price", 0.0))
    if not vwap or price < vwap:
        return None
    if minute_context.get("previous_price", price) > vwap:
        return None
    if snapshot.get("buy_trade_ratio_5s", 0.0) < cfg["buy_trade_ratio_5s"]:
        return None
    if snapshot.get("spread_pct", 999.0) > cfg["spread_pct"]:
        return None
    if snapshot.get("micro_state") not in {"ACCELERATING", "STABLE"}:
        return None
    return _candidate({**snapshot, "market": market}, "VWAP_RECLAIM", {"vwap": vwap, "last_price": price})
