from __future__ import annotations


def build_ws_forward_candidate_features(session_summary: dict, priority_strategies: list[str] | None = None) -> list[dict]:
    strategies = priority_strategies or ["VWAP_PULLBACK", "EMA_PULLBACK", "ORDERBOOK_IMBALANCE"]
    markets = session_summary.get("markets", [])
    rows = []
    for market in markets:
        trade_count = session_summary.get("trade_event_count_by_market", {}).get(market, 0)
        orderbook_count = session_summary.get("orderbook_event_count_by_market", {}).get(market, 0)
        for strategy in strategies:
            if trade_count == 0 and orderbook_count == 0:
                decision = "CANCEL"
                reason = "DATA_QUALITY_POOR"
            elif strategy == "ORDERBOOK_IMBALANCE" and orderbook_count == 0:
                decision = "WAIT"
                reason = "ORDERBOOK_UNAVAILABLE"
            else:
                decision = "WAIT"
                reason = "MICRO_STATE_WEAK"
            rows.append({"market": market, "strategy_id": strategy, "trade_event_count": trade_count, "orderbook_event_count": orderbook_count, "entry_decision": decision, "primary_block_reason": reason, "orderbook_available": orderbook_count > 0})
    return rows
