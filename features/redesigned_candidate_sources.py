from __future__ import annotations

from uuid import uuid4

from features.breakout_precondition_features import compute_breakout_preconditions
from features.orderflow_precondition_features import compute_orderflow_preconditions
from features.volume_acceleration_features import compute_volume_acceleration


def detect_volume_range_breakout_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    breakout = compute_breakout_preconditions(snapshot)
    volume = compute_volume_acceleration(snapshot)
    if breakout["breakout_precondition_score"] >= 50 and volume["volume_acceleration"] and float(snapshot.get("spread_pct", 999)) <= 0.25:
        return _candidate(snapshot, "VOLUME_RANGE_BREAKOUT", {**breakout, **volume}, "B")
    return None


def detect_orderflow_surge_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    orderflow = compute_orderflow_preconditions(snapshot)
    if orderflow["orderflow_score"] >= 45 and float(snapshot.get("spread_pct", 999)) <= 0.25:
        return _candidate(snapshot, "ORDERFLOW_SURGE", orderflow, "B")
    return None


def detect_vwap_reclaim_with_volume_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    volume = compute_volume_acceleration(snapshot)
    if float(snapshot.get("vwap_distance_pct", 0.0)) >= 0 and volume["volume_acceleration"] and float(snapshot.get("buy_trade_ratio_10s", 0.0)) >= 0.5:
        return _candidate(snapshot, "VWAP_RECLAIM_WITH_VOLUME", volume, "B")
    return None


def detect_early_volume_accumulation_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    volume = compute_volume_acceleration(snapshot)
    if volume["volume_acceleration"] and 0 <= float(snapshot.get("price_change_10s_pct", 0.0)) <= 0.12:
        return _candidate(snapshot, "EARLY_VOLUME_ACCUMULATION", volume, "B")
    return None


def detect_range_compression_expansion_candidate(snapshot: dict, config: dict | None = None) -> dict | None:
    if float(snapshot.get("previous_high_distance_pct", 999)) <= 0.2 and float(snapshot.get("price_change_10s_pct", 0.0)) >= 0:
        return _candidate(snapshot, "RANGE_COMPRESSION_EXPANSION", {"previous_high_distance_pct": snapshot.get("previous_high_distance_pct")}, "B")
    return None


def detect_redesigned_candidates(snapshot: dict) -> list[dict]:
    checks = [
        detect_volume_range_breakout_candidate,
        detect_orderflow_surge_candidate,
        detect_vwap_reclaim_with_volume_candidate,
        detect_early_volume_accumulation_candidate,
        detect_range_compression_expansion_candidate,
    ]
    return [candidate for check in checks for candidate in [check(snapshot)] if candidate]


def _candidate(snapshot: dict, source: str, evidence: dict, grade: str) -> dict:
    price = float(snapshot.get("last_price", snapshot.get("reference_price", 0.0)))
    return {
        "candidate_id": f"{source.lower()}_{uuid4().hex[:10]}",
        "market": snapshot.get("market", ""),
        "candidate_time_ms": int(snapshot.get("timestamp_ms", 0)),
        "candidate_source": source,
        "reference_price": price,
        "expected_target_pct": 0.7 if grade in {"A", "S"} else 0.35,
        "expected_stop_pct": 0.25,
        "evidence": evidence,
        "signal_grade_hint": grade,
        "risk_flags": [],
        "data_source": "UPBIT_WS",
        "research_mode": True,
        "real_order_enabled": False,
    }
