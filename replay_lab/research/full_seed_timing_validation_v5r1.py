from __future__ import annotations


def validate_full_seed_timing_v5r1(initial_cash_krw: float = 500000) -> dict:
    return {"initial_cash_krw": initial_cash_krw, "default_sizing_mode": "FULL_SEED_LADDER", "real_order_enabled": False, "research_mode": True}
