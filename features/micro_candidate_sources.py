from __future__ import annotations

from uuid import uuid4


def detect_micro_acceleration_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    cfg = {"price_change_3s_pct": 0.05, "price_change_5s_pct": 0.08, "buy_trade_ratio_5s": 0.52, "spread_pct": 0.20, "micro_strength_score": 55.0, **(config or {})}
    if snapshot.get("price_change_3s_pct", 0.0) < cfg["price_change_3s_pct"]:
        return None
    if snapshot.get("price_change_5s_pct", 0.0) < cfg["price_change_5s_pct"]:
        return None
    if snapshot.get("buy_trade_ratio_5s", 0.0) < cfg["buy_trade_ratio_5s"]:
        return None
    if snapshot.get("spread_pct", 999.0) > cfg["spread_pct"]:
        return None
    if snapshot.get("micro_strength_score", 0.0) < cfg["micro_strength_score"]:
        return None
    return _candidate(snapshot, "MICRO_ACCELERATION", {"price_change_3s_pct": snapshot.get("price_change_3s_pct"), "buy_trade_ratio_5s": snapshot.get("buy_trade_ratio_5s")})


def _candidate(snapshot: dict, source: str, evidence: dict) -> dict:
    price = float(snapshot.get("last_price", 0.0))
    return {"candidate_id": f"{source.lower()}_{uuid4().hex[:10]}", "session_id": snapshot.get("session_id", ""), "market": snapshot["market"], "candidate_time_ms": snapshot["timestamp_ms"], "candidate_source": source, "reference_price": price, "expected_target_pct": 0.35, "expected_stop_pct": 0.20, "evidence": evidence, "risk_flags": [], "data_source": "UPBIT_WS", "real_order_enabled": False}
