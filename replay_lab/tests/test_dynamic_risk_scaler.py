from __future__ import annotations

from portfolio.dynamic_risk_scaler import DynamicRiskScaler


def test_dynamic_risk_scaler_uses_recorded_previous_trades_only():
    scaler = DynamicRiskScaler()
    assert scaler.stats(20).trade_count == 0
    scaler.record(1000, "2025-01-01")
    scaler.record(-500, "2025-01-02")

    stats = scaler.stats(20)
    audit = scaler.audit_window(20)

    assert stats.trade_count == 2
    assert stats.profit_factor == 2.0
    assert audit["rolling_window_end_time"] == "2025-01-02"
