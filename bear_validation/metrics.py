from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RISK_STATES = {"EDGE_DECAY", "BTC_LED_MARKET", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}


def profit_factor(rows: list[dict[str, Any]]) -> float:
    pnls = [float(row.get("pnl_krw", 0.0)) for row in rows if row.get("defense_action", "ENTER") == "ENTER"]
    wins = sum(pnl for pnl in pnls if pnl > 0.0)
    losses = abs(sum(pnl for pnl in pnls if pnl < 0.0))
    if losses:
        return wins / losses
    return 99.0 if wins else 0.0


def period_rows(journal: list[dict[str, Any]], mode: str = "month") -> list[dict[str, Any]]:
    key_len = {"day": 10, "month": 7, "year": 4}[mode]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        period = str(row.get("date", ""))[:key_len]
        if period:
            groups[period].append(row)
    out = []
    for period in sorted(groups):
        rows = groups[period]
        start = float(rows[0].get("equity_before", 0.0))
        end = float(rows[-1].get("equity_after", 0.0))
        out.append(
            {
                "period": period,
                "trade_count": sum(1 for row in rows if row.get("defense_action") == "ENTER"),
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": end - start,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": min([0.0] + [float(row.get("drawdown_pct", 0.0)) for row in rows]),
                "profit_factor": profit_factor(rows),
            }
        )
    return out


def summary_from_journal(name: str, journal: list[dict[str, Any]], initial_cash_krw: float) -> dict[str, Any]:
    final = float(journal[-1].get("equity_after", initial_cash_krw)) if journal else initial_cash_krw
    entered = [row for row in journal if row.get("defense_action") == "ENTER"]
    pnls = [float(row.get("pnl_krw", 0.0)) for row in entered]
    mdd = min([0.0] + [float(row.get("drawdown_pct", 0.0)) for row in journal])
    ret = (final / initial_cash_krw - 1.0) * 100.0 if initial_cash_krw else 0.0
    return {
        "scenario": name,
        "final_equity_krw": final,
        "return_pct": ret,
        "mdd_pct": mdd,
        "profit_factor": profit_factor(entered),
        "return_mdd_ratio": ret / abs(mdd) if mdd else 0.0,
        "trade_count": len(entered),
        "skipped_trade_count": len(journal) - len(entered),
        "win_rate_pct": sum(1 for pnl in pnls if pnl > 0.0) / len(pnls) * 100.0 if pnls else 0.0,
        "lookahead_fail_count": sum(1 for row in journal if row.get("lookahead_check") != "PASS"),
    }


def saved_loss_vs(candidate: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> dict[str, float]:
    saved = missed = 0.0
    for row, base in zip(candidate, baseline):
        pnl = float(row.get("pnl_krw", 0.0))
        base_pnl = float(base.get("pnl_krw", 0.0))
        diff = pnl - base_pnl
        if base_pnl < 0.0 and diff > 0.0:
            saved += diff
        elif base_pnl > 0.0 and diff < 0.0:
            missed += abs(diff)
    return {"saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed}


def most_common(rows: list[dict[str, Any]], key: str) -> str:
    values = [str(row.get(key) or "") for row in rows if row.get(key)]
    return Counter(values).most_common(1)[0][0] if values else "UNKNOWN"


def hwm_giveback(journal: list[dict[str, Any]], initial_cash_krw: float) -> dict[str, float]:
    final = float(journal[-1].get("equity_after", initial_cash_krw)) if journal else initial_cash_krw
    peak = max([initial_cash_krw] + [float(row.get("equity_after", initial_cash_krw)) for row in journal])
    giveback = peak - final
    return {
        "high_watermark_krw": peak,
        "hwm_giveback_krw": giveback,
        "hwm_giveback_pct": giveback / peak * 100.0 if peak else 0.0,
    }
