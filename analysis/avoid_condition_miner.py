from __future__ import annotations

from analysis.strategy_failure_reason_analyzer import analyze_strategy_failure


def mine_avoid_conditions(strategy: str, trades: list[dict]) -> list[str]:
    return analyze_strategy_failure(strategy, trades)["avoid_conditions"]
