from __future__ import annotations


def compound_trade_pnl(base_pnl_krw: float, equity_before: float, base_equity_krw: float = 500000) -> float:
    if base_equity_krw <= 0:
        return 0.0
    return base_pnl_krw * (equity_before / base_equity_krw)


def return_pct_from_equity(pnl_krw: float, equity_before: float) -> float:
    return pnl_krw / equity_before * 100 if equity_before else 0.0
