from __future__ import annotations


def build_micro_feature_snapshot(market: str, now_ms: int, trade_events: list[dict], orderbook_events: list[dict], lookback_seconds: int = 10) -> dict:
    trades = [event for event in trade_events if event.get("market") == market and 0 <= now_ms - int(event.get("timestamp_ms", now_ms)) <= lookback_seconds * 1000]
    orderbooks = [event for event in orderbook_events if event.get("market") == market and int(event.get("timestamp_ms", 0)) <= now_ms]
    warnings = []
    if not trades:
        return _empty(market, now_ms, ["no_recent_trades"])
    last_price = float(trades[-1].get("trade_price", 0.0))
    latest_ob = orderbooks[-1] if orderbooks else {}
    if not orderbooks:
        warnings.append("orderbook_unavailable")
    best_ask, best_bid, ask_size, bid_size = _top_orderbook(latest_ob)
    spread_pct = (best_ask - best_bid) / last_price * 100 if best_ask and best_bid and last_price else 999.0
    bid_ask_size_ratio = bid_size / ask_size if ask_size else 0.0
    imbalance = (bid_size - ask_size) / (bid_size + ask_size) if (bid_size + ask_size) else 0.0
    snapshot = {
        "market": market,
        "timestamp_ms": now_ms,
        "last_price": last_price,
        "price_change_1s_pct": _price_change(trades, now_ms, 1, last_price),
        "price_change_3s_pct": _price_change(trades, now_ms, 3, last_price),
        "price_change_5s_pct": _price_change(trades, now_ms, 5, last_price),
        "price_change_10s_pct": _price_change(trades, now_ms, 10, last_price),
        "volume_1s": _volume(trades, now_ms, 1),
        "volume_3s": _volume(trades, now_ms, 3),
        "volume_5s": _volume(trades, now_ms, 5),
        "volume_10s": _volume(trades, now_ms, 10),
        "buy_trade_volume_1s": _volume(trades, now_ms, 1, "BID"),
        "buy_trade_volume_3s": _volume(trades, now_ms, 3, "BID"),
        "buy_trade_volume_5s": _volume(trades, now_ms, 5, "BID"),
        "buy_trade_volume_10s": _volume(trades, now_ms, 10, "BID"),
        "sell_trade_volume_1s": _volume(trades, now_ms, 1, "ASK"),
        "sell_trade_volume_3s": _volume(trades, now_ms, 3, "ASK"),
        "sell_trade_volume_5s": _volume(trades, now_ms, 5, "ASK"),
        "sell_trade_volume_10s": _volume(trades, now_ms, 10, "ASK"),
        "buy_trade_ratio_1s": _buy_ratio(trades, now_ms, 1),
        "buy_trade_ratio_3s": _buy_ratio(trades, now_ms, 3),
        "buy_trade_ratio_5s": _buy_ratio(trades, now_ms, 5),
        "buy_trade_ratio_10s": _buy_ratio(trades, now_ms, 10),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_pct": spread_pct,
        "top_bid_size": bid_size,
        "top_ask_size": ask_size,
        "bid_ask_size_ratio": bid_ask_size_ratio,
        "orderbook_imbalance": imbalance,
        "warnings": warnings,
    }
    snapshot["micro_strength_score"] = _strength(snapshot)
    snapshot["micro_state"] = _state(snapshot)
    return snapshot


def _top_orderbook(orderbook: dict) -> tuple[float, float, float, float]:
    units = orderbook.get("units") or []
    if not units:
        return 0.0, 0.0, 0.0, 0.0
    top = units[0]
    return float(top.get("ask_price", 0.0)), float(top.get("bid_price", 0.0)), float(top.get("ask_size", 0.0)), float(top.get("bid_size", 0.0))


def _price_change(trades: list[dict], now_ms: int, seconds: int, last_price: float) -> float:
    cutoff = now_ms - seconds * 1000
    prior = [event for event in trades if int(event.get("timestamp_ms", 0)) <= cutoff]
    base = float((prior[-1] if prior else trades[0]).get("trade_price", 0.0))
    return (last_price - base) / base * 100 if base else 0.0


def _volume(trades: list[dict], now_ms: int, seconds: int, side: str | None = None) -> float:
    cutoff = now_ms - seconds * 1000
    rows = [event for event in trades if int(event.get("timestamp_ms", 0)) >= cutoff and (side is None or str(event.get("ask_bid", "")).upper() == side)]
    return sum(float(event.get("trade_volume", 0.0)) for event in rows)


def _buy_ratio(trades: list[dict], now_ms: int, seconds: int) -> float:
    buy = _volume(trades, now_ms, seconds, "BID")
    sell = _volume(trades, now_ms, seconds, "ASK")
    return buy / (buy + sell) if (buy + sell) else 0.5


def _strength(snapshot: dict) -> float:
    score = 45 + snapshot["price_change_3s_pct"] * 180 + (snapshot["buy_trade_ratio_5s"] - 0.5) * 80 + max(0.0, snapshot["orderbook_imbalance"]) * 40
    if snapshot["spread_pct"] <= 0.2:
        score += 10
    return max(0.0, min(100.0, score))


def _state(snapshot: dict) -> str:
    if snapshot["micro_strength_score"] >= 60 and snapshot["price_change_3s_pct"] >= 0.03:
        return "ACCELERATING"
    if snapshot["price_change_5s_pct"] >= 0 and snapshot["buy_trade_ratio_5s"] >= 0.5:
        return "STABLE"
    if snapshot["price_change_3s_pct"] < -0.05:
        return "REVERSING"
    return "FADING"


def _empty(market: str, now_ms: int, warnings: list[str]) -> dict:
    return {"market": market, "timestamp_ms": now_ms, "last_price": 0.0, "price_change_1s_pct": 0.0, "price_change_3s_pct": 0.0, "price_change_5s_pct": 0.0, "price_change_10s_pct": 0.0, "volume_1s": 0.0, "volume_3s": 0.0, "volume_5s": 0.0, "volume_10s": 0.0, "buy_trade_ratio_1s": 0.0, "buy_trade_ratio_3s": 0.0, "buy_trade_ratio_5s": 0.0, "buy_trade_ratio_10s": 0.0, "spread_pct": 999.0, "bid_ask_size_ratio": 0.0, "orderbook_imbalance": 0.0, "micro_state": "NO_DATA", "micro_strength_score": 0.0, "warnings": warnings}
