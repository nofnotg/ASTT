from __future__ import annotations


def calculate_spread_pct(best_bid: float, best_ask: float) -> float:
    if best_bid <= 0 or best_ask <= 0:
        return 999.0
    mid = (best_bid + best_ask) / 2
    return ((best_ask - best_bid) / mid) * 100 if mid else 999.0


def calculate_spread_contraction(previous_spread_pct: float, current_spread_pct: float) -> float:
    if previous_spread_pct <= 0:
        return 0.0
    return max(-1.0, min(1.0, (previous_spread_pct - current_spread_pct) / previous_spread_pct))
