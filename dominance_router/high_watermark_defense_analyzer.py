from __future__ import annotations

from typing import Any


def analyze_high_watermark(journal: list[dict[str, Any]]) -> dict[str, Any]:
    peak = None
    trough = None
    peak_date = None
    trough_date = None
    events: list[dict[str, Any]] = []
    for row in journal:
        equity = _num(row.get("equity_after"))
        date = row.get("date") or row.get("entry_time") or row.get("decision_time")
        if peak is None or equity > peak:
            if peak is not None and trough is not None and trough < peak:
                events.append(_event(peak, trough, peak_date, trough_date, row))
            peak, trough = equity, equity
            peak_date, trough_date = date, date
        elif trough is None or equity < trough:
            trough, trough_date = equity, date
    if peak is not None and trough is not None and trough < peak:
        events.append(_event(peak, trough, peak_date, trough_date, journal[-1] if journal else {}))
    worst = min((event["drawdown_pct"] for event in events), default=0.0)
    return {
        "peak_defense_events": events,
        "max_giveback_pct": worst,
        "high_watermark_preservation_score": max(0.0, 100.0 + worst),
    }


def _event(peak: float, trough: float, peak_date: Any, trough_date: Any, row: dict[str, Any]) -> dict[str, Any]:
    drawdown = (trough / peak - 1.0) * 100.0 if peak else 0.0
    return {
        "peak_date": peak_date,
        "trough_date": trough_date,
        "peak_equity": peak,
        "trough_equity": trough,
        "drawdown_pct": drawdown,
        "active_market_state": row.get("market_state"),
        "active_agent": row.get("scenario") or row.get("selected_agent_before_trade"),
        "saved_loss": 0.0,
        "missed_profit": 0.0,
        "would_control_have_lost_more": False,
    }


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
