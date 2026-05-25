from __future__ import annotations

from portfolio.equity_curve_simulator import simulate_equity_curve


def build_trade_journal(initial_cash_krw: float = 500000, compounding: bool = True) -> dict:
    result = simulate_equity_curve(initial_cash_krw, compounding)
    return {
        "schema_version": "v6.2",
        "trade_count": result["trade_count"],
        "initial_cash_krw": result["initial_cash_krw"],
        "final_equity_krw": result["final_equity_krw"],
        "journal": result["journal"],
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
