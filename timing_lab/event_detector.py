from __future__ import annotations

from collections import Counter
from typing import Any

from timing_lab.ring_buffer import MarketRingBuffer
from timing_lab.timing_event_schema import TimingEvent, make_event_id


class EventDetector:
    def __init__(self, initial_cash_krw: float = 500000):
        self.initial_cash_krw = float(initial_cash_krw)

    def detect(self, buffer: MarketRingBuffer, market: str) -> list[dict[str, Any]]:
        rows = buffer.get_events(market)
        if not rows:
            return []
        events: list[TimingEvent] = []
        events.extend(_detect_volume_spike(market, rows))
        events.extend(_detect_orderflow_shift(market, rows))
        events.extend(_detect_spread_contraction(market, rows))
        events.extend(_detect_depth_recovery(market, rows, self.initial_cash_krw))
        events.extend(_detect_range_touch(market, rows))
        events.extend(_detect_breakout_pressure(market, rows))
        events.extend(_detect_btc_shock(market, rows))
        events.extend(_detect_market_rank_surge(market, rows))
        deduped = {}
        for event in events:
            deduped[event.event_id] = event.to_dict()
        return list(deduped.values())


def detect_events_from_rows(rows: list[dict[str, Any]], initial_cash_krw: float = 500000) -> list[dict[str, Any]]:
    buffer = MarketRingBuffer(1800)
    for row in sorted(rows, key=lambda item: int(item.get("timestamp_ms", 0))):
        market = row.get("market") or row.get("code") or "UNKNOWN"
        buffer.append(market, row)
    detector = EventDetector(initial_cash_krw)
    events: list[dict[str, Any]] = []
    for market in buffer.markets():
        events.extend(detector.detect(buffer, market))
    return events


def _event(market: str, event_type: str, row: dict[str, Any], evidence: dict[str, Any], severity: str = "LOW") -> TimingEvent:
    ts = int(row.get("timestamp_ms", 0))
    price = float(row.get("trade_price") or row.get("price") or evidence.get("reference_price") or 0.0)
    return TimingEvent(make_event_id(market, event_type, ts), market, event_type, ts, price, evidence, severity)


def _trades(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("type") == "trade" and float(row.get("trade_price") or 0) > 0]


def _orderbooks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("type") == "orderbook"]


def _detect_volume_spike(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    trades = _trades(rows)
    if len(trades) < 3:
        return []
    newest = trades[-1]
    end = int(newest["timestamp_ms"])
    recent = [r for r in trades if int(r["timestamp_ms"]) >= end - 30_000]
    baseline = [r for r in trades if end - 300_000 <= int(r["timestamp_ms"]) < end - 30_000]
    recent_value = sum(float(r.get("trade_price", 0)) * float(r.get("trade_volume", 0)) for r in recent)
    baseline_avg = sum(float(r.get("trade_price", 0)) * float(r.get("trade_volume", 0)) for r in baseline) / max(1, len(baseline) / 6)
    ratio = recent_value / baseline_avg if baseline_avg > 0 else (2.0 if recent_value > 0 else 0.0)
    return [_event(market, "VOLUME_SPIKE", newest, {"volume_30s_krw": recent_value, "volume_5m_avg_krw": baseline_avg, "ratio": ratio}, "MEDIUM" if ratio >= 2 else "LOW")] if ratio >= 2 else []


def _detect_orderflow_shift(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    trades = _trades(rows)
    if len(trades) < 3:
        return []
    newest = trades[-1]
    end = int(newest["timestamp_ms"])
    recent = [r for r in trades if int(r["timestamp_ms"]) >= end - 30_000]
    if not recent:
        return []
    counts = Counter(r.get("ask_bid") for r in recent)
    buy_ratio = counts.get("BID", 0) / len(recent)
    return [_event(market, "ORDERFLOW_SHIFT", newest, {"buy_trade_ratio_30s": buy_ratio, "trade_count_30s": len(recent)}, "MEDIUM")] if buy_ratio >= 0.6 else []


def _detect_spread_contraction(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    orderbooks = _orderbooks(rows)
    if len(orderbooks) < 2:
        return []
    spreads = [_spread_pct(row) for row in orderbooks if _spread_pct(row) is not None]
    if len(spreads) < 2:
        return []
    latest = spreads[-1]
    avg_prev = sum(spreads[:-1]) / len(spreads[:-1])
    return [_event(market, "SPREAD_CONTRACTION", orderbooks[-1], {"spread_pct": latest, "previous_avg_spread_pct": avg_prev}, "LOW")] if latest < avg_prev * 0.75 else []


def _detect_depth_recovery(market: str, rows: list[dict[str, Any]], initial_cash_krw: float) -> list[TimingEvent]:
    orderbooks = _orderbooks(rows)
    if not orderbooks:
        return []
    latest_depth = _ask_depth_krw(orderbooks[-1])
    prev_depths = [_ask_depth_krw(row) for row in orderbooks[:-1]]
    prev_avg = sum(prev_depths) / max(1, len(prev_depths))
    if latest_depth >= initial_cash_krw and latest_depth > prev_avg * 1.25:
        return [_event(market, "DEPTH_RECOVERY", orderbooks[-1], {"depth_3_level_krw": latest_depth, "previous_avg_depth_krw": prev_avg}, "MEDIUM")]
    return []


def _detect_range_touch(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    trades = _trades(rows)
    if len(trades) < 3:
        return []
    prices = [float(r["trade_price"]) for r in trades]
    latest = prices[-1]
    high = max(prices[:-1])
    if high > 0 and abs(latest - high) / high <= 0.001:
        return [_event(market, "RANGE_TOUCH", trades[-1], {"range_high": high, "latest_price": latest}, "LOW")]
    return []


def _detect_breakout_pressure(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    trades = _trades(rows)
    if len(trades) < 4:
        return []
    prices = [float(r["trade_price"]) for r in trades]
    if prices[-1] > max(prices[:-1]) and sum(1 for r in trades[-4:] if r.get("ask_bid") == "BID") >= 3:
        return [_event(market, "BREAKOUT_PRESSURE", trades[-1], {"previous_high": max(prices[:-1]), "latest_price": prices[-1], "recent_bid_trades": 3}, "HIGH")]
    return []


def _detect_btc_shock(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    if market != "KRW-BTC":
        return []
    trades = _trades(rows)
    if len(trades) < 2:
        return []
    first = float(trades[0]["trade_price"])
    latest = float(trades[-1]["trade_price"])
    change_pct = (latest - first) / first * 100 if first else 0.0
    return [_event(market, "BTC_SHOCK", trades[-1], {"window_change_pct": change_pct}, "MEDIUM")] if abs(change_pct) >= 0.1 else []


def _detect_market_rank_surge(market: str, rows: list[dict[str, Any]]) -> list[TimingEvent]:
    tickers = [row for row in rows if row.get("type") == "ticker"]
    if not tickers:
        return []
    raw = tickers[-1].get("raw", {}) if isinstance(tickers[-1].get("raw"), dict) else {}
    acc = float(raw.get("acc_trade_price_24h") or raw.get("acc_trade_price") or 0)
    return [_event(market, "MARKET_RANK_SURGE", tickers[-1], {"acc_trade_price_24h": acc}, "LOW")] if acc > 0 else []


def _spread_pct(row: dict[str, Any]) -> float | None:
    units = row.get("units") or row.get("orderbook_units") or row.get("raw", {}).get("orderbook_units", [])
    if not units:
        return None
    ask = float(units[0].get("ask_price") or 0)
    bid = float(units[0].get("bid_price") or 0)
    mid = (ask + bid) / 2 if ask and bid else 0
    return (ask - bid) / mid * 100 if mid else None


def _ask_depth_krw(row: dict[str, Any], levels: int = 3) -> float:
    units = row.get("units") or row.get("orderbook_units") or row.get("raw", {}).get("orderbook_units", [])
    return sum(float(unit.get("ask_price") or 0) * float(unit.get("ask_size") or 0) for unit in units[:levels])
