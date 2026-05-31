from __future__ import annotations


def adverse_slippage_price(price: float, side: str, slippage_pct: float) -> float:
    if side == "sell":
        return price * (1.0 - slippage_pct / 100.0)
    return price * (1.0 + slippage_pct / 100.0)
