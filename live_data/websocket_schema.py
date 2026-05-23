from __future__ import annotations

from datetime import datetime


def normalize_trade_tick(payload: dict) -> dict:
    return {
        "market": payload.get("code") or payload.get("market", ""),
        "trade_price": float(payload.get("trade_price", 0.0)),
        "trade_volume": float(payload.get("trade_volume", 0.0)),
        "ask_bid": payload.get("ask_bid", ""),
        "trade_timestamp": payload.get("trade_timestamp") or payload.get("timestamp") or datetime.utcnow().isoformat(),
        "best_ask_price": float(payload.get("best_ask_price", 0.0)),
        "best_ask_size": float(payload.get("best_ask_size", 0.0)),
        "best_bid_price": float(payload.get("best_bid_price", 0.0)),
        "best_bid_size": float(payload.get("best_bid_size", 0.0)),
    }


def normalize_orderbook_tick(payload: dict) -> dict:
    units = payload.get("orderbook_units") or [{}]
    top = units[0] if units else {}
    return {
        "market": payload.get("code") or payload.get("market", ""),
        "ask_price": float(top.get("ask_price", payload.get("ask_price", 0.0))),
        "bid_price": float(top.get("bid_price", payload.get("bid_price", 0.0))),
        "ask_size": float(top.get("ask_size", payload.get("ask_size", 0.0))),
        "bid_size": float(top.get("bid_size", payload.get("bid_size", 0.0))),
        "total_ask_size": float(payload.get("total_ask_size", 0.0)),
        "total_bid_size": float(payload.get("total_bid_size", 0.0)),
        "timestamp": payload.get("timestamp") or datetime.utcnow().isoformat(),
    }
