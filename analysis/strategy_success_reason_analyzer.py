from __future__ import annotations

from collections import Counter


def analyze_strategy_success(strategy: str, trades: list[dict]) -> dict:
    wins = [row for row in trades if row.get("pnl_krw", 0) > 0]
    setups = Counter(row.get("setup_type", "UNKNOWN") for row in wins)
    markets = Counter(row.get("market", "UNKNOWN") for row in wins)
    return {
        "strategy": strategy,
        "winning_trade_count": len(wins),
        "surviving_setups": [name for name, _ in setups.most_common(5)],
        "common_conditions": ["positive_pnl", "stop_target_defined", "risk_based_position_size"],
        "favorable_regimes": ["ALT_ROTATION", "HIGH_VOLATILITY"] if wins else [],
        "favorable_mtf_structure": ["MTF setup score available"],
        "favorable_stop_target_conditions": ["rr>=1.2", "bounded stop distance"],
        "top_markets": [name for name, _ in markets.most_common(5)],
    }
