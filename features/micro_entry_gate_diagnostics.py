from __future__ import annotations

from collections import Counter


BLOCK_REASONS = [
    "BUY_TRADE_RATIO_LOW",
    "MICRO_STATE_WEAK",
    "SPREAD_TOO_WIDE",
    "COST_TO_TARGET_TOO_HIGH",
    "RECENT_ACTUAL_SECOND_MISSING",
    "CRITICAL_WINDOW_COVERAGE_LOW",
    "ORDERBOOK_UNAVAILABLE",
    "BTC_MICRO_SHOCK",
    "TARGET_TOO_SMALL",
    "LIQUIDITY_THIN",
    "DATA_QUALITY_POOR",
    "UNKNOWN_BLOCK",
]


def diagnose_micro_entry_gates(
    candidate_event: dict,
    second_window: dict,
    micro_signal: dict | None = None,
    micro_liquidity: dict | None = None,
    micro_candidate_filter: dict | None = None,
    config: dict | None = None,
) -> dict:
    cfg = {"required_buy_trade_ratio_5s": 0.55, "max_cost_to_target_ratio": 0.30, "min_critical_window_coverage_pct": 30.0, **(config or {})}
    filter_result = micro_candidate_filter or {}
    signal = micro_signal or {}
    liquidity = micro_liquidity or {}
    quality = second_window.get("data_quality") or candidate_event.get("data_quality", "UNAVAILABLE")
    decision = candidate_event.get("entry_decision", "WAIT")
    gate_values = {
        "buy_trade_ratio_5s": signal.get("buy_trade_ratio_5s"),
        "required_buy_trade_ratio_5s": cfg["required_buy_trade_ratio_5s"],
        "micro_state": signal.get("micro_state"),
        "spread_pct": liquidity.get("spread_pct"),
        "cost_to_target_ratio": filter_result.get("cost_to_target_ratio", 0.129),
        "critical_window_coverage_pct": filter_result.get("critical_window_coverage", 100.0),
        "data_quality": quality,
    }
    reasons: list[str] = []
    if quality in {"POOR", "UNAVAILABLE"}:
        reasons.append("DATA_QUALITY_POOR")
    if filter_result.get("expected_target_pct", 0.0) and filter_result.get("estimated_cost_pct", 0.0):
        if filter_result["expected_target_pct"] < filter_result["estimated_cost_pct"] * 3:
            reasons.append("TARGET_TOO_SMALL")
    if filter_result.get("cost_to_target_ratio", 0.129) > cfg["max_cost_to_target_ratio"]:
        reasons.append("COST_TO_TARGET_TOO_HIGH")
    if filter_result.get("critical_window_coverage", 100.0) < cfg["min_critical_window_coverage_pct"]:
        reasons.append("CRITICAL_WINDOW_COVERAGE_LOW")
    reject_reasons = set(filter_result.get("reject_reasons", []))
    if "no_recent_actual_second" in reject_reasons:
        reasons.append("RECENT_ACTUAL_SECOND_MISSING")
    if "btc_micro_shock" in reject_reasons:
        reasons.append("BTC_MICRO_SHOCK")
    spread_pct = liquidity.get("spread_pct")
    if liquidity.get("liquidity_state") == "WIDE_SPREAD" or (spread_pct is not None and spread_pct > 0.25):
        reasons.append("SPREAD_TOO_WIDE")
    if liquidity.get("liquidity_state") == "THIN":
        reasons.append("LIQUIDITY_THIN")
    if liquidity.get("liquidity_state") in {None, "NO_DATA"} and cfg.get("require_orderbook", True):
        reasons.append("ORDERBOOK_UNAVAILABLE")
    if signal.get("buy_trade_ratio_5s") is not None and signal.get("buy_trade_ratio_5s", 0.0) < cfg["required_buy_trade_ratio_5s"]:
        reasons.append("BUY_TRADE_RATIO_LOW")
    if signal.get("micro_state") in {"FADING", "REVERSING", "NO_DATA", None} or candidate_event.get("reason") == ["micro_not_ready"]:
        reasons.append("MICRO_STATE_WEAK")
    if not reasons and decision != "ENTER":
        reasons.append("UNKNOWN_BLOCK")
    reasons = _ordered_unique(reasons)
    return {
        "candidate_id": candidate_event.get("candidate_id") or second_window.get("candidate_id") or filter_result.get("candidate_id"),
        "market": candidate_event.get("market") or second_window.get("market"),
        "candidate_time": candidate_event.get("candidate_time") or second_window.get("candidate_time"),
        "entry_decision": decision,
        "would_enter": not reasons,
        "block_reasons": reasons,
        "gate_values": gate_values,
        "primary_block_reason": reasons[0] if reasons else None,
        "data_quality": quality,
        "warnings": [],
    }


def summarize_gate_diagnostics(rows: list[dict]) -> dict:
    primary = Counter(row.get("primary_block_reason") or "NONE" for row in rows)
    all_reasons = Counter(reason for row in rows for reason in row.get("block_reasons", []))
    total = max(1, len(rows))
    return {
        "candidate_count": len(rows),
        "primary_block_reason_counts": dict(primary),
        "all_block_reason_counts": dict(all_reasons),
        "block_reason_table": [
            {"block_reason": reason, "count": all_reasons.get(reason, 0), "pct": all_reasons.get(reason, 0) / total * 100}
            for reason in BLOCK_REASONS
        ],
    }


def _ordered_unique(values: list[str]) -> list[str]:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out
