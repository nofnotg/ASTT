from __future__ import annotations


def apply_fill_costs(gross_pnl_krw: float, position_krw: float, fee_pct: float = 0.05, slippage_pct: float = 0.10) -> dict[str, float]:
    fee = abs(position_krw) * fee_pct / 100.0 * 2.0
    slippage = abs(position_krw) * slippage_pct / 100.0
    return {"gross_pnl_krw": gross_pnl_krw, "fee_krw": fee, "slippage_krw": slippage, "net_pnl_krw": gross_pnl_krw - fee - slippage}
