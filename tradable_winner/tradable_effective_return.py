from __future__ import annotations


def calculate_tradable_effective_return(
    raw_return_pct: float,
    entry_spread_cost_pct: float,
    exit_spread_cost_pct: float,
    slippage_pct: float,
    fee_pct: float = 0.05,
) -> dict:
    total_cost = max(0.0, entry_spread_cost_pct) + max(0.0, exit_spread_cost_pct) + max(0.0, slippage_pct) + max(0.0, fee_pct)
    effective_return = raw_return_pct - total_cost
    reward_to_cost = raw_return_pct / total_cost if total_cost > 0 else 999.0
    return {
        "raw_return_pct": raw_return_pct,
        "estimated_total_cost_pct": total_cost,
        "effective_return_pct": effective_return,
        "reward_to_cost_ratio": reward_to_cost,
    }
