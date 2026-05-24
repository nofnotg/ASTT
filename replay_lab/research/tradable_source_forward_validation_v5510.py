from __future__ import annotations

from execution.tradable_source_forward_runner import run_tradable_source_forward_validation_v5510


def validate_tradable_source_recorded_v5510(sessions_dir: str, initial_cash_krw: float) -> dict:
    return run_tradable_source_forward_validation_v5510("RECORDED_VALIDATION", initial_cash_krw, True, 0)


def run_tradable_source_live_smoke_v5510(duration_minutes: int, top_markets: int, initial_cash_krw: float, research_mode: bool) -> dict:
    return run_tradable_source_forward_validation_v5510("LIVE_FORWARD_SMOKE", initial_cash_krw, research_mode, duration_minutes)


def run_tradable_source_live_forward_v5510(duration_minutes: int, top_markets: int, initial_cash_krw: float, research_mode: bool) -> dict:
    return run_tradable_source_forward_validation_v5510("LIVE_FORWARD_60M", initial_cash_krw, research_mode, duration_minutes)
