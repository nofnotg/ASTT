from __future__ import annotations

from execution.redesigned_source_forward_runner import run_redesigned_source_forward_test_v559


def run_redesigned_source_forward_test_research_v559(duration_minutes: int, top_markets: int, sources: str, initial_cash_krw: float, scenario: str, research_mode: bool) -> dict:
    return run_redesigned_source_forward_test_v559(duration_minutes, top_markets, sources, initial_cash_krw, scenario, research_mode)
