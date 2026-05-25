from __future__ import annotations

from strategy_engine.v61_strategy_runner import run_v61_strategy_robustness


def run_v61_strategy_robustness_backtest(months: int = 36, initial_cash_krw: float = 500000, paper_entry_policy: str = "ACTIVE_RESEARCH") -> dict:
    return run_v61_strategy_robustness(months, initial_cash_krw, paper_entry_policy)
