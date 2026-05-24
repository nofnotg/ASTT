from __future__ import annotations


def compute_orderflow_preconditions(snapshot: dict) -> dict:
    buy_ratio = float(snapshot.get("buy_trade_ratio_10s", 0.0))
    imbalance = float(snapshot.get("orderbook_imbalance", 0.0))
    return {"buy_pressure": buy_ratio >= 0.55, "orderbook_support": imbalance > 0.05, "orderflow_score": min(100.0, buy_ratio * 70 + max(0.0, imbalance) * 60)}
