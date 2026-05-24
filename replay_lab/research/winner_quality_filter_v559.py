from __future__ import annotations

from winner_mining.winner_quality_filter import filter_winner_quality


def run_winner_quality_filter_v559(winner_traces: str, initial_cash_krw: float = 500000) -> dict:
    return filter_winner_quality(winner_traces, initial_cash_krw)
