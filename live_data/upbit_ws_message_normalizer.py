from __future__ import annotations

from datetime import datetime


def normalize_upbit_trade_message(raw: dict) -> dict:
    return {
        "data_source": "UPBIT_WS",
        "type": "trade",
        "market": raw.get("code") or raw.get("market", ""),
        "timestamp_ms": int(raw.get("trade_timestamp") or raw.get("timestamp") or _now_ms()),
        "received_at_ms": _now_ms(),
        "trade_price": float(raw.get("trade_price", 0.0)),
        "trade_volume": float(raw.get("trade_volume", 0.0)),
        "ask_bid": raw.get("ask_bid", ""),
        "sequential_id": raw.get("sequential_id", 0),
        "best_ask_price": float(raw.get("best_ask_price", 0.0) or 0.0),
        "best_ask_size": float(raw.get("best_ask_size", 0.0) or 0.0),
        "best_bid_price": float(raw.get("best_bid_price", 0.0) or 0.0),
        "best_bid_size": float(raw.get("best_bid_size", 0.0) or 0.0),
        "stream_type": raw.get("stream_type", ""),
        "raw": raw,
    }


def normalize_upbit_orderbook_message(raw: dict) -> dict:
    units = raw.get("orderbook_units") or raw.get("units") or []
    return {
        "data_source": "UPBIT_WS",
        "type": "orderbook",
        "market": raw.get("code") or raw.get("market", ""),
        "timestamp_ms": int(raw.get("timestamp") or _now_ms()),
        "received_at_ms": _now_ms(),
        "total_ask_size": float(raw.get("total_ask_size", 0.0) or 0.0),
        "total_bid_size": float(raw.get("total_bid_size", 0.0) or 0.0),
        "units": [
            {"ask_price": float(u.get("ask_price", 0.0)), "bid_price": float(u.get("bid_price", 0.0)), "ask_size": float(u.get("ask_size", 0.0)), "bid_size": float(u.get("bid_size", 0.0))}
            for u in units
        ],
        "raw": raw,
    }


def _now_ms() -> int:
    return int(datetime.utcnow().timestamp() * 1000)
