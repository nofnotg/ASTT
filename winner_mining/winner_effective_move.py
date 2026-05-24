from __future__ import annotations


def calculate_effective_move(
    raw_return_pct: float,
    entry_spread_pct: float = 0.0,
    exit_spread_pct: float = 0.0,
    slippage_pct: float = 0.05,
    fee_pct: float = 0.05,
) -> dict:
    cost_pct = max(0.0, entry_spread_pct / 2) + max(0.0, exit_spread_pct / 2) + slippage_pct + fee_pct
    effective_return_pct = raw_return_pct - cost_pct
    return {
        "raw_return_pct": raw_return_pct,
        "estimated_entry_spread_pct": entry_spread_pct,
        "estimated_exit_spread_pct": exit_spread_pct,
        "estimated_slippage_pct": slippage_pct,
        "fee_pct": fee_pct,
        "estimated_total_cost_pct": cost_pct,
        "effective_return_pct": effective_return_pct,
        "reward_to_cost_ratio": raw_return_pct / cost_pct if cost_pct else 999.0,
    }
