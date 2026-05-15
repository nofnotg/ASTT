from __future__ import annotations


def conservative_bid_fill(best_ask: float, slippage_pct: float) -> tuple[float, float]:
    fill_price = best_ask * (1 + slippage_pct / 100)
    return fill_price, max(0.0, fill_price - best_ask)


def conservative_ask_fill(best_bid: float, slippage_pct: float) -> tuple[float, float]:
    fill_price = best_bid * (1 - slippage_pct / 100)
    return fill_price, max(0.0, best_bid - fill_price)

