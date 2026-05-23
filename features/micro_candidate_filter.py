from __future__ import annotations

import pandas as pd

from features.micro_cost_model import SCENARIOS
from features.micro_signal_features import compute_micro_signal_features


def apply_micro_candidate_filter(
    candidate_event: dict,
    second_window: dict,
    market_context: dict | None = None,
    config: dict | None = None,
) -> dict:
    cfg = {
        "min_cost_multiple_pass": 5.0,
        "min_cost_multiple_watch": 3.0,
        "min_critical_coverage_pct": 30.0,
        "cost_scenario": "realistic_1",
        **(config or {}),
    }
    candidate_id = second_window.get("candidate_id") or candidate_event.get("candidate_id", "")
    quality = second_window.get("quality") or {}
    seconds = pd.DataFrame(second_window.get("seconds", []))
    candidate_time = pd.Timestamp(candidate_event.get("candidate_time") or second_window.get("candidate_time"))
    if seconds.empty:
        return _decision(candidate_id, "REJECT", 0.0, [], ["second_window_empty"], 0.0, _estimated_cost(cfg), 1.0, 0.0, 0.0)
    seconds["time"] = pd.to_datetime(seconds["time"])
    pre = seconds[seconds["time"] <= candidate_time].copy()
    signal = compute_micro_signal_features(pre, as_of_time=candidate_time)
    expected_target_pct = _expected_target_pct(candidate_event)
    estimated_cost_pct = _estimated_cost(cfg)
    cost_to_target_ratio = estimated_cost_pct / expected_target_pct if expected_target_pct > 0 else 999.0
    actual_coverage = float(quality.get("actual_coverage_pct", _coverage(seconds)))
    critical_coverage = float(quality.get("critical_window_coverage_pct", _critical_coverage(seconds, candidate_time)))
    recent_actual = _has_recent_actual(pre, candidate_time, seconds=10)
    reject = []
    reasons = []
    if expected_target_pct < estimated_cost_pct * cfg["min_cost_multiple_watch"]:
        reject.append("target_too_small_vs_cost")
    if critical_coverage <= 0:
        reject.append("critical_window_no_actual_seconds")
    if not recent_actual:
        reject.append("no_recent_actual_second")
    if signal.get("micro_state") == "REVERSING":
        reject.append("micro_state_reversing")
    if market_context and market_context.get("btc_micro_shock"):
        reject.append("btc_micro_shock")
    if reject:
        return _decision(candidate_id, "REJECT", _score(expected_target_pct, estimated_cost_pct, critical_coverage, actual_coverage, signal), reasons, reject, expected_target_pct, estimated_cost_pct, cost_to_target_ratio, actual_coverage, critical_coverage)
    if expected_target_pct >= estimated_cost_pct * cfg["min_cost_multiple_pass"] and critical_coverage >= cfg["min_critical_coverage_pct"] and recent_actual:
        reasons.extend(["target_cost_ratio_pass", "critical_coverage_pass", f"micro_state_{signal.get('micro_state', 'unknown').lower()}"])
        return _decision(candidate_id, "PASS", _score(expected_target_pct, estimated_cost_pct, critical_coverage, actual_coverage, signal), reasons, [], expected_target_pct, estimated_cost_pct, cost_to_target_ratio, actual_coverage, critical_coverage)
    reasons.extend(["watch_only_until_cost_or_coverage_improves"])
    return _decision(candidate_id, "WATCH", _score(expected_target_pct, estimated_cost_pct, critical_coverage, actual_coverage, signal), reasons, [], expected_target_pct, estimated_cost_pct, cost_to_target_ratio, actual_coverage, critical_coverage)


def _estimated_cost(config: dict) -> float:
    scenario = SCENARIOS.get(config.get("cost_scenario", "realistic_1"), SCENARIOS["realistic_1"])
    latency_cost = scenario["latency_ms"] / 1000 * 0.01
    return scenario["fee_pct"] * 2 + scenario["slippage_pct"] + latency_cost


def _expected_target_pct(candidate_event: dict) -> float:
    ref = float(candidate_event.get("reference_price") or candidate_event.get("entry_price") or 0.0)
    target = float(candidate_event.get("target_price") or 0.0)
    if not ref or not target:
        return 0.0
    return max(0.0, (target - ref) / ref * 100)


def _coverage(seconds: pd.DataFrame) -> float:
    return float((~seconds.get("synthetic", pd.Series([False] * len(seconds))).astype(bool)).mean() * 100) if len(seconds) else 0.0


def _critical_coverage(seconds: pd.DataFrame, candidate_time: pd.Timestamp) -> float:
    critical = seconds[(seconds["time"] >= candidate_time - pd.Timedelta(seconds=10)) & (seconds["time"] <= candidate_time + pd.Timedelta(seconds=30))]
    return _coverage(critical)


def _has_recent_actual(pre: pd.DataFrame, candidate_time: pd.Timestamp, seconds: int) -> bool:
    recent = pre[(pre["time"] >= candidate_time - pd.Timedelta(seconds=seconds)) & (pre["time"] <= candidate_time)]
    if recent.empty or "synthetic" not in recent:
        return False
    return bool((~recent["synthetic"].astype(bool)).any())


def _score(expected_target_pct: float, estimated_cost_pct: float, critical_coverage: float, actual_coverage: float, signal: dict) -> float:
    ratio_score = min(40.0, (expected_target_pct / max(estimated_cost_pct, 0.0001)) * 8)
    coverage_score = min(35.0, critical_coverage * 0.7)
    actual_score = min(15.0, actual_coverage * 0.3)
    momentum_score = 10.0 if signal.get("micro_state") in {"ACCELERATING", "STABLE"} else 0.0
    return round(min(100.0, ratio_score + coverage_score + actual_score + momentum_score), 4)


def _decision(candidate_id: str, decision: str, score: float, reasons: list[str], reject_reasons: list[str], expected_target_pct: float, estimated_cost_pct: float, cost_to_target_ratio: float, actual_coverage: float, critical_coverage: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "micro_candidate_decision": decision,
        "score": score,
        "reasons": reasons,
        "reject_reasons": reject_reasons,
        "expected_target_pct": expected_target_pct,
        "estimated_cost_pct": estimated_cost_pct,
        "cost_to_target_ratio": cost_to_target_ratio,
        "actual_second_coverage": actual_coverage,
        "critical_window_coverage": critical_coverage,
    }
