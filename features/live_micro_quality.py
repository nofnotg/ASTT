from __future__ import annotations

import pandas as pd


def evaluate_live_micro_quality(trades, orderbooks, candidate_events=None) -> dict:
    trade_frame = pd.DataFrame(trades or [])
    ob_frame = pd.DataFrame(orderbooks or [])
    if trade_frame.empty and ob_frame.empty:
        return _result(0.0, "UNAVAILABLE", 0.0, 0.0, 999.0, 1.0, ["no_micro_data"])
    trade_coverage = 100.0 if not trade_frame.empty else 0.0
    orderbook_coverage = 100.0 if not ob_frame.empty else 0.0
    gaps = []
    for frame in [trade_frame, ob_frame]:
        if not frame.empty and "timestamp_ms" in frame:
            gaps.extend(pd.to_numeric(frame["timestamp_ms"], errors="coerce").sort_values().diff().dropna().div(1000).tolist())
    max_gap = max(gaps) if gaps else 0.0
    missing_ob = 0.0 if orderbook_coverage else 1.0
    score = min(trade_coverage, orderbook_coverage) - min(max_gap, 30)
    if trade_coverage and orderbook_coverage and max_gap <= 5:
        grade = "GOOD"
    elif trade_coverage and max_gap <= 20:
        grade = "PARTIAL"
    elif trade_coverage or orderbook_coverage:
        grade = "POOR"
    else:
        grade = "UNAVAILABLE"
    warnings = []
    if missing_ob:
        warnings.append("orderbook_missing")
    if max_gap > 10:
        warnings.append("event_gap")
    return _result(max(0.0, score), grade, trade_coverage, orderbook_coverage, max_gap, missing_ob, warnings)


def _result(score, grade, trade_coverage, orderbook_coverage, max_gap, missing_ob, warnings) -> dict:
    return {"quality_score": score, "quality_grade": grade, "trade_coverage_pct": trade_coverage, "orderbook_coverage_pct": orderbook_coverage, "max_event_gap_seconds": max_gap, "missing_orderbook_ratio": missing_ob, "warnings": warnings}
