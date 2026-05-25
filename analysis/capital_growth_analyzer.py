from __future__ import annotations

from execution.v6_position_manager import summarize_v6_trades


def summarize_capital_growth(journal: list[dict], initial_cash_krw: float) -> dict:
    perf = summarize_v6_trades(journal, initial_cash_krw)
    best = max(journal, key=lambda row: row["pnl_krw"]) if journal else None
    worst = min(journal, key=lambda row: row["pnl_krw"]) if journal else None
    return {
        **perf,
        "final_equity_krw": journal[-1]["equity_after"] if journal else initial_cash_krw,
        "max_drawdown_pct": min((row["drawdown_pct"] for row in journal), default=0.0),
        "best_trade": best["trade_id"] if best else None,
        "worst_trade": worst["trade_id"] if worst else None,
    }
