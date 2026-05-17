from __future__ import annotations


STRATEGY_IDS = ["MTF_ONLY", "ZONE_ONLY", "MTF_PLUS_ZONE"]


def build_edge_signal(seed_trade: dict, strategy_id: str) -> dict:
    daily = float(seed_trade.get("daily_structure_score", 0.0))
    h4 = float(seed_trade.get("h4_flow_score", 0.0))
    zone_score = float(seed_trade.get("v5_score", 0.0))
    trigger = float(seed_trade.get("v5_score", 0.0))
    entry = float(seed_trade.get("entry_price", 0.0))
    stop = float(seed_trade.get("zone_stop", entry * 0.992 if entry else 0.0))
    score = _score(strategy_id, daily, h4, zone_score, trigger)
    allowed = _allowed(strategy_id, daily, h4, zone_score, trigger)
    return {
        "strategy_id": strategy_id,
        "market": seed_trade.get("market", ""),
        "as_of_time": seed_trade.get("signal_time_kst", seed_trade.get("entry_time_kst", "")),
        "entry_allowed": bool(allowed),
        "entry_price": entry,
        "stop_price": stop,
        "strategy_score": score,
        "setup_reasons": _reasons(strategy_id, daily, h4, zone_score),
        "warnings": [] if allowed else ["threshold_not_met"],
        "components": {
            "daily": {"score": daily},
            "h4": {"score": h4},
            "zone": {"score": zone_score},
            "trigger": {"score": trigger},
            "risk": {"risk_pct": (entry - stop) / entry * 100 if entry else 0.0},
        },
    }


def _score(strategy_id: str, daily: float, h4: float, zone: float, trigger: float) -> float:
    if strategy_id == "MTF_ONLY":
        return daily * 0.4 + h4 * 0.4 + trigger * 0.2
    if strategy_id == "ZONE_ONLY":
        return zone * 0.7 + trigger * 0.3
    return daily * 0.3 + h4 * 0.3 + zone * 0.25 + trigger * 0.15


def _allowed(strategy_id: str, daily: float, h4: float, zone: float, trigger: float) -> bool:
    if strategy_id == "MTF_ONLY":
        return daily >= 55 and h4 >= 50 and trigger >= 70
    if strategy_id == "ZONE_ONLY":
        return zone >= 70 and trigger >= 70
    return daily >= 55 and h4 >= 50 and zone >= 70 and trigger >= 70


def _reasons(strategy_id: str, daily: float, h4: float, zone: float) -> list[str]:
    reasons = [f"strategy={strategy_id}"]
    if daily >= 55:
        reasons.append("daily_ok")
    if h4 >= 50:
        reasons.append("h4_ok")
    if zone >= 70:
        reasons.append("zone_ok")
    return reasons
