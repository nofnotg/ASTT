from __future__ import annotations


def breakdown_micro_momentum(snapshot: dict, config: dict | None = None) -> dict:
    cfg = {"min_price_change_3s_pct": 0.03, "min_buy_trade_ratio_5s": 0.52, "min_volume_5s": 0.000001, "min_orderbook_imbalance": 0.05, "max_spread_pct": 0.20, **(config or {})}
    reasons = []
    components = {
        "price_acceleration_score": max(0.0, min(100.0, snapshot.get("price_change_3s_pct", 0.0) / cfg["min_price_change_3s_pct"] * 100)) if cfg["min_price_change_3s_pct"] else 0.0,
        "buy_pressure_score": max(0.0, min(100.0, snapshot.get("buy_trade_ratio_5s", 0.0) / cfg["min_buy_trade_ratio_5s"] * 100)) if cfg["min_buy_trade_ratio_5s"] else 0.0,
        "volume_burst_score": 100.0 if snapshot.get("volume_5s", 0.0) >= cfg["min_volume_5s"] else 0.0,
        "orderbook_score": max(0.0, min(100.0, snapshot.get("orderbook_imbalance", 0.0) / cfg["min_orderbook_imbalance"] * 100)) if cfg["min_orderbook_imbalance"] else 0.0,
        "spread_score": 100.0 if snapshot.get("spread_pct", 999.0) <= cfg["max_spread_pct"] else 0.0,
    }
    if snapshot.get("price_change_3s_pct", 0.0) < cfg["min_price_change_3s_pct"]:
        reasons.append("PRICE_ACCELERATION_LOW")
    if snapshot.get("buy_trade_ratio_5s", 0.0) < cfg["min_buy_trade_ratio_5s"]:
        reasons.append("BUY_TRADE_RATIO_LOW")
    if snapshot.get("volume_5s", 0.0) < cfg["min_volume_5s"]:
        reasons.append("VOLUME_BURST_ABSENT")
    if snapshot.get("spread_pct", 999.0) > cfg["max_spread_pct"]:
        reasons.append("SPREAD_NOT_FAVORABLE")
    if snapshot.get("orderbook_imbalance", 0.0) < cfg["min_orderbook_imbalance"]:
        reasons.append("ORDERBOOK_IMBALANCE_ABSENT")
    if snapshot.get("price_change_1s_pct", 0.0) < 0 and snapshot.get("price_change_5s_pct", 0.0) > 0:
        reasons.append("MOVE_ALREADY_EXHAUSTED")
    if snapshot.get("micro_state") == "NO_DATA":
        reasons.append("DATA_TOO_THIN")
    return {"micro_state": snapshot.get("micro_state", "NO_DATA"), "weak_reasons": reasons, "strength_components": components, "micro_strength_score": snapshot.get("micro_strength_score", 0.0)}
