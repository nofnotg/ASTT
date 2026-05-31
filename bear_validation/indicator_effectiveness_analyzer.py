from __future__ import annotations

from typing import Any, Callable

from bear_validation.metrics import RISK_STATES


IndicatorFn = Callable[[dict[str, Any]], bool]


def indicator_rows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions: list[tuple[str, IndicatorFn]] = [
        ("200MA_REGIME_PROXY", lambda row: str(row.get("btc_trend")) == "DOWN" or str(row.get("market_state")) in {"BEAR_DEFENSE", "LOCKDOWN"}),
        ("BTCDOM_DOMINANCE_REGIME", lambda row: str(row.get("market_state")) in RISK_STATES or "SPIKE" in str(row.get("dominance_regime"))),
        ("HMM_RISK_OFF_PROXY", lambda row: str(row.get("market_state")) in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}),
        ("MARKET_BREADTH_PROXY", lambda row: str(row.get("market_state")) in {"EDGE_DECAY", "RISK_OFF_ALT_WEAK"}),
        ("STRATEGY_HEALTH", lambda row: bool(row.get("guard_on")) or float(row.get("recent_pf", 99.0)) < 1.0 or float(row.get("current_month_return_pct", 0.0)) <= -3.0),
    ]
    return [_effectiveness(name, fn, journal) for name, fn in definitions]


def _effectiveness(name: str, fn: IndicatorFn, journal: list[dict[str, Any]]) -> dict[str, Any]:
    risk_off = [row for row in journal if fn(row)]
    risk_on = [row for row in journal if not fn(row)]
    saved = missed = 0.0
    false_alarm = 0
    for row in risk_off:
        pnl = float(row.get("pnl_krw", 0.0))
        capped = pnl * 0.35
        if pnl < 0.0:
            saved += capped - pnl
        elif pnl > 0.0:
            missed += pnl - capped
            false_alarm += 1
    decision = "INDICATOR_CANDIDATE" if saved > missed and len(risk_off) >= 10 else "RESEARCH_ONLY"
    return {
        "indicator": name,
        "risk_on_trade_count": len(risk_on),
        "risk_off_trade_count": len(risk_off),
        "risk_on_pnl": sum(float(row.get("pnl_krw", 0.0)) for row in risk_on),
        "risk_off_pnl": sum(float(row.get("pnl_krw", 0.0)) for row in risk_off),
        "false_alarm": false_alarm,
        "saved_loss": saved,
        "missed_profit": missed,
        "net_effect": saved - missed,
        "decision": decision,
    }
