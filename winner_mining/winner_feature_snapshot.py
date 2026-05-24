from __future__ import annotations


def compute_winner_feature_snapshot(trades: list[dict], orderbooks: list[dict] | None = None, as_of_ms: int | None = None, lookback_seconds: int = 60) -> dict:
    if as_of_ms is None and trades:
        as_of_ms = int(trades[-1].get("timestamp_ms", 0))
    as_of_ms = int(as_of_ms or 0)
    prior = [event for event in trades if int(event.get("timestamp_ms", 0)) <= as_of_ms and as_of_ms - int(event.get("timestamp_ms", 0)) <= lookback_seconds * 1000]
    if not prior:
        return _empty()
    first = float(prior[0].get("trade_price", 0.0))
    last = float(prior[-1].get("trade_price", 0.0))
    buy = sum(float(e.get("trade_volume", 0.0)) for e in prior if str(e.get("ask_bid", "")).upper() == "BID")
    volume = sum(float(e.get("trade_volume", 0.0)) for e in prior)
    high = max(float(e.get("trade_price", 0.0)) for e in prior)
    low = min(float(e.get("trade_price", 0.0)) for e in prior)
    ob = _latest_orderbook(orderbooks or [], as_of_ms)
    spread_pct, bid_ask_size_ratio, imbalance = _orderbook_features(ob, last)
    return {
        "price_change_pct": (last - first) / first * 100 if first else 0.0,
        "range_position_pct": (last - low) / (high - low) * 100 if high > low else 50.0,
        "previous_high_distance_pct": (high - last) / last * 100 if last else 0.0,
        "breakout_distance_pct": (last - high) / high * 100 if high else 0.0,
        "volume": volume,
        "buy_trade_ratio": buy / volume if volume else 0.5,
        "trade_count": len(prior),
        "spread_pct": spread_pct,
        "bid_ask_size_ratio": bid_ask_size_ratio,
        "orderbook_imbalance": imbalance,
        "vwap_distance_pct": _vwap_distance(prior, last),
        "ema20_distance_pct": 0.0,
        "ema50_distance_pct": 0.0,
    }


def _latest_orderbook(orderbooks: list[dict], as_of_ms: int) -> dict:
    rows = [ob for ob in orderbooks if int(ob.get("timestamp_ms", 0)) <= as_of_ms]
    return rows[-1] if rows else {}


def _orderbook_features(orderbook: dict, price: float) -> tuple[float, float, float]:
    units = orderbook.get("units") or []
    if not units:
        return 999.0, 0.0, 0.0
    top = units[0]
    ask = float(top.get("ask_price", 0.0))
    bid = float(top.get("bid_price", 0.0))
    ask_size = float(top.get("ask_size", 0.0))
    bid_size = float(top.get("bid_size", 0.0))
    spread = (ask - bid) / price * 100 if ask and bid and price else 999.0
    ratio = bid_size / ask_size if ask_size else 0.0
    imbalance = (bid_size - ask_size) / (bid_size + ask_size) if bid_size + ask_size else 0.0
    return spread, ratio, imbalance


def _vwap_distance(trades: list[dict], last: float) -> float:
    value = sum(float(e.get("trade_price", 0.0)) * float(e.get("trade_volume", 0.0)) for e in trades)
    volume = sum(float(e.get("trade_volume", 0.0)) for e in trades)
    vwap = value / volume if volume else last
    return (last - vwap) / vwap * 100 if vwap else 0.0


def _empty() -> dict:
    return {"price_change_pct": 0.0, "range_position_pct": 0.0, "previous_high_distance_pct": 0.0, "breakout_distance_pct": 0.0, "volume": 0.0, "buy_trade_ratio": 0.0, "trade_count": 0, "spread_pct": 999.0, "bid_ask_size_ratio": 0.0, "orderbook_imbalance": 0.0, "vwap_distance_pct": 0.0, "ema20_distance_pct": 0.0, "ema50_distance_pct": 0.0}
