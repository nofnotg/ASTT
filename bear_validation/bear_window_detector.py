from __future__ import annotations

from typing import Any

from bear_validation.metrics import most_common, period_rows, profit_factor


def detect_bear_windows(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    months = period_rows(journal, "month")
    rows_by_month = {row["period"]: [item for item in journal if str(item.get("date", ""))[:7] == row["period"]] for row in months}
    windows: list[dict[str, Any]] = []
    for month in months:
        period = str(month["period"])
        rows = rows_by_month[period]
        if not rows:
            continue
        pf20 = profit_factor(rows[-20:])
        recent10 = rows[-10:]
        recent20 = rows[-20:]
        loss10 = sum(1 for row in recent10 if float(row.get("pnl_krw", 0.0)) < 0.0)
        cum20 = sum(float(row.get("pnl_krw", 0.0)) for row in recent20)
        hwm_dd = min([0.0] + [float(row.get("drawdown_pct", 0.0)) for row in rows])
        reasons = []
        if float(month["return_pct"]) <= -3.0:
            reasons.append("MONTHLY_RETURN_LE_-3")
        if pf20 < 1.0:
            reasons.append("PF20_LT_1")
        if hwm_dd <= -8.0:
            reasons.append("HWM_DRAWDOWN_LE_-8")
        if loss10 >= 7:
            reasons.append("RECENT_10_LOSS_GE_7")
        if cum20 < 0.0:
            reasons.append("RECENT_20_CUM_PNL_LT_0")
        if not reasons:
            continue
        windows.append(
            {
                "window": f"BW-{period}",
                "start_time": str(rows[0].get("entry_time") or rows[0].get("date")),
                "end_time": str(rows[-1].get("exit_time") or rows[-1].get("date")),
                "trigger_reason": ",".join(reasons),
                "active_route_pnl": float(month["pnl_krw"]),
                "active_route_mdd": hwm_dd,
                "PF20": pf20,
                "monthly_return_pct": float(month["return_pct"]),
                "HWM_drawdown": hwm_dd,
                "BTC_trend": most_common(rows, "btc_trend"),
                "dominance_regime": most_common(rows, "dominance_regime"),
                "market_state": most_common(rows, "market_state"),
                "recommended_test_group": _group(reasons, rows),
            }
        )
    return windows


def _group(reasons: list[str], rows: list[dict[str, Any]]) -> str:
    states = {str(row.get("market_state")) for row in rows}
    if "HWM_DRAWDOWN_LE_-8" in reasons or "MONTHLY_RETURN_LE_-3" in reasons:
        return "LOSS_GUARD_INDICATOR_LAB"
    if states & {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}:
        return "BEAR_ROUTER_LAB"
    if "PF20_LT_1" in reasons:
        return "STRATEGY_HEALTH_LAB"
    return "INDICATOR_EFFECTIVENESS_LAB"
