from __future__ import annotations

from collections import Counter


def analyze_strategy_failure(strategy: str, trades: list[dict]) -> dict:
    losses = [row for row in trades if row.get("pnl_krw", 0) <= 0]
    setups = Counter(row.get("setup_type", "UNKNOWN") for row in losses)
    reasons = ["failed_follow_through", "fees_after_breakeven", "stop_hit_or_time_exit"]
    if strategy.startswith("DADDY"):
        reasons.append("volume_location_signal_not_sufficient_alone")
    return {
        "strategy": strategy,
        "losing_trade_count": len(losses),
        "failed_setups": [name for name, _ in setups.most_common(5)],
        "avoid_conditions": reasons,
        "unfavorable_regimes": ["CHOP", "BULL_WITH_WEAK_FOLLOW_THROUGH"],
        "loss_repetition_pattern": "small losses repeat before occasional large winner" if losses else "none",
        "disable_candidates": [name for name, count in setups.items() if count >= 3],
    }
