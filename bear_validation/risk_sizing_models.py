from __future__ import annotations

from typing import Any

from bear_validation.metrics import RISK_STATES, hwm_giveback, summary_from_journal


def apply_sizing_model(name: str, source: list[dict[str, Any]], initial_cash_krw: float) -> dict[str, Any]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    journal: list[dict[str, Any]] = []
    for idx, row in enumerate(source):
        before = equity
        factor = _factor(name, row, source[max(0, idx - 20) : idx])
        pnl = float(row.get("pnl_krw", 0.0)) * factor
        if name == "ATR_TRAILING_STOP" and pnl < 0.0:
            pnl *= 0.70
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        drawdown = (equity / peak - 1.0) * 100.0 if peak else 0.0
        new_row = dict(row)
        new_row.update(
            {
                "scenario": name,
                "equity_before": before,
                "equity_after": equity,
                "pnl_krw": pnl,
                "drawdown_pct": drawdown,
                "risk_multiplier_after_defense": float(row.get("risk_multiplier_after_defense", 1.0)) * factor,
            }
        )
        journal.append(new_row)
    summary = summary_from_journal(name, journal, initial_cash_krw)
    summary.update(hwm_giveback(journal, initial_cash_krw))
    summary["decision"] = "RISK_SIZING_CANDIDATE" if summary["mdd_pct"] > summary_from_journal("BASE", source, initial_cash_krw)["mdd_pct"] else "RESEARCH_ONLY"
    return {"summary": summary, "journal": journal}


def _factor(name: str, row: dict[str, Any], recent: list[dict[str, Any]]) -> float:
    state = str(row.get("market_state") or "")
    dd = float(row.get("drawdown_before_pct", row.get("drawdown_pct", 0.0)))
    if name == "FIXED_MULTIPLIER":
        return 1.0
    if name == "VOLATILITY_TARGETING":
        return 0.35 if state in RISK_STATES or dd <= -8.0 else 0.85
    if name == "ATR_POSITION_SIZING":
        return 0.45 if state in RISK_STATES else 0.75
    if name == "ATR_TRAILING_STOP":
        return 0.95
    if name == "FRACTIONAL_KELLY_0.1":
        wins = sum(float(item.get("pnl_krw", 0.0)) for item in recent if float(item.get("pnl_krw", 0.0)) > 0)
        losses = abs(sum(float(item.get("pnl_krw", 0.0)) for item in recent if float(item.get("pnl_krw", 0.0)) < 0))
        pf = wins / losses if losses else 2.0
        return 0.35 if pf < 1.0 else 0.65
    return 1.0
