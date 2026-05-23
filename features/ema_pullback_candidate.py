from __future__ import annotations

from features.micro_candidate_sources import _candidate


def detect_ema_pullback_candidate(market: str, snapshot: dict, minute_context: dict, config: dict | None = None) -> dict | None:
    cfg = {"buy_trade_ratio_5s": 0.52, "max_distance_to_ema20_pct": 0.25, **(config or {})}
    ema20 = float(minute_context.get("ema20", 0.0))
    ema50 = float(minute_context.get("ema50", 0.0))
    price = float(snapshot.get("last_price", 0.0))
    if not ema20 or not ema50 or ema20 < ema50:
        return None
    distance = abs(price - ema20) / ema20 * 100 if ema20 else 999.0
    if distance > cfg["max_distance_to_ema20_pct"]:
        return None
    if snapshot.get("price_change_5s_pct", 0.0) <= 0:
        return None
    if snapshot.get("buy_trade_ratio_5s", 0.0) < cfg["buy_trade_ratio_5s"]:
        return None
    return _candidate({**snapshot, "market": market}, "EMA_PULLBACK", {"ema20": ema20, "ema50": ema50, "distance_to_ema20_pct": distance})
