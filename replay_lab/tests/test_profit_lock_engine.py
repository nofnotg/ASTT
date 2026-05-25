from __future__ import annotations

from portfolio.profit_lock_engine import ProfitLockEngine


def test_profit_lock_reduces_risk_after_large_monthly_gain():
    engine = ProfitLockEngine(500000)
    assert engine.monthly_multiplier_cap("2025-01", 500000)[0] == 1.5

    cap, reasons = engine.monthly_multiplier_cap("2025-01", 560000)

    assert cap == 0.5
    assert "PROFIT_LOCK_MONTHLY_10" in reasons
