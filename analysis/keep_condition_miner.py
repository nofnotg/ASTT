from __future__ import annotations

from analysis.strategy_success_reason_analyzer import analyze_strategy_success


def mine_keep_conditions(strategy: str, trades: list[dict]) -> list[str]:
    return analyze_strategy_success(strategy, trades)["common_conditions"]
