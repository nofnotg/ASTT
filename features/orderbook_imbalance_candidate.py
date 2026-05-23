from __future__ import annotations

from features.micro_candidate_sources import _candidate


def detect_orderbook_imbalance_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    cfg = {"bid_ask_size_ratio": 1.2, "orderbook_imbalance": 0.10, "buy_trade_ratio_3s": 0.52, "spread_pct": 0.20, **(config or {})}
    if snapshot.get("bid_ask_size_ratio", 0.0) < cfg["bid_ask_size_ratio"]:
        return None
    if snapshot.get("orderbook_imbalance", 0.0) < cfg["orderbook_imbalance"]:
        return None
    if snapshot.get("buy_trade_ratio_3s", 0.0) < cfg["buy_trade_ratio_3s"]:
        return None
    if snapshot.get("spread_pct", 999.0) > cfg["spread_pct"]:
        return None
    return _candidate(snapshot, "ORDERBOOK_IMBALANCE", {"bid_ask_size_ratio": snapshot.get("bid_ask_size_ratio"), "orderbook_imbalance": snapshot.get("orderbook_imbalance")})
