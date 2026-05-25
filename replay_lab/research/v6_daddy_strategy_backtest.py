from __future__ import annotations

from execution.v6_paper_entry_runner import run_v6_strategy_backtest


def run_v6_daddy_backtest(months: int, initial_cash_krw: float, paper_entry_policy: str) -> dict:
    return run_v6_strategy_backtest("DADDY_VOLUME_NECKLINE", months, initial_cash_krw, paper_entry_policy)
