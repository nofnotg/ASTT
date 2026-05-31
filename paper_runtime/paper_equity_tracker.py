from __future__ import annotations


def apply_pnl(equity_krw: float, pnl_krw: float) -> float:
    return max(0.0, float(equity_krw) + float(pnl_krw))
