from __future__ import annotations


TRADABLE_WINNER_TYPES = ("TRADABLE_SCALP_WINNER", "TRADABLE_MOMENTUM_WINNER", "TRADABLE_SPIKE_WINNER")

WINNER_TYPE_CONFIG = {
    "TRADABLE_SCALP_WINNER": {
        "min_seconds": 180,
        "max_seconds": 300,
        "min_effective_return_pct": 0.35,
        "min_reward_to_cost": 3.0,
        "max_spread_pct": 0.20,
        "depth_3_required_krw": 1_000_000,
        "depth_5_required_krw": 1_000_000,
        "slippage_pct": 0.05,
    },
    "TRADABLE_MOMENTUM_WINNER": {
        "min_seconds": 300,
        "max_seconds": 900,
        "min_effective_return_pct": 0.80,
        "min_reward_to_cost": 3.5,
        "max_spread_pct": 0.20,
        "depth_3_required_krw": 1_500_000,
        "depth_5_required_krw": 1_500_000,
        "slippage_pct": 0.07,
    },
    "TRADABLE_SPIKE_WINNER": {
        "min_seconds": 900,
        "max_seconds": 1800,
        "min_effective_return_pct": 1.50,
        "min_reward_to_cost": 4.0,
        "max_spread_pct": 0.20,
        "depth_3_required_krw": 1_500_000,
        "depth_5_required_krw": 2_000_000,
        "slippage_pct": 0.10,
    },
}
