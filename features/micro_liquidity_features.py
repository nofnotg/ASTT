from __future__ import annotations

import pandas as pd


def compute_micro_liquidity_features(orderbook_ticks, as_of_time=None) -> dict:
    ticks = pd.DataFrame(orderbook_ticks or [])
    if ticks.empty:
        return {"best_ask_price": 0.0, "best_bid_price": 0.0, "spread_pct": 999.0, "top_bid_size": 0.0, "top_ask_size": 0.0, "bid_ask_size_ratio": 0.0, "orderbook_imbalance": 0.0, "liquidity_state": "NO_DATA", "warnings": ["orderbook_unavailable"]}
    if "timestamp" in ticks:
        ticks["time"] = pd.to_datetime(ticks["timestamp"], errors="coerce")
    if as_of_time is not None and "time" in ticks:
        ticks = ticks[ticks["time"] <= pd.Timestamp(as_of_time)]
    row = ticks.iloc[-1]
    ask = float(row.get("best_ask_price", row.get("ask_price", 0.0)))
    bid = float(row.get("best_bid_price", row.get("bid_price", 0.0)))
    ask_size = float(row.get("best_ask_size", row.get("ask_size", 0.0)))
    bid_size = float(row.get("best_bid_size", row.get("bid_size", 0.0)))
    mid = (ask + bid) / 2 if ask and bid else 0.0
    spread = (ask - bid) / mid * 100 if mid else 999.0
    ratio = bid_size / ask_size if ask_size else 0.0
    imbalance = (bid_size - ask_size) / (bid_size + ask_size) if (bid_size + ask_size) else 0.0
    state = "GOOD"
    warnings = []
    if spread > 0.25:
        state = "WIDE_SPREAD"
        warnings.append("wide_spread")
    elif ask_size + bid_size <= 0:
        state = "THIN"
        warnings.append("thin_orderbook")
    elif ratio >= 1.5:
        state = "BID_SUPPORT"
    elif ratio <= 0.5:
        state = "ASK_WALL"
    return {"best_ask_price": ask, "best_bid_price": bid, "spread_pct": spread, "top_bid_size": bid_size, "top_ask_size": ask_size, "bid_ask_size_ratio": ratio, "orderbook_imbalance": imbalance, "liquidity_state": state, "warnings": warnings}
