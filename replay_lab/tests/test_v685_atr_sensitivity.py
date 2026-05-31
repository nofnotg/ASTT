from __future__ import annotations

from atr_validation.atr_sensitivity_lab import sensitivity_factor


def test_v685_atr_sensitivity_changes_by_model_and_timeframe() -> None:
    conservative = sensitivity_factor(14, 2.0, "1h", "conservative")
    optimistic = sensitivity_factor(14, 2.0, "1h", "optimistic")
    five_minute = sensitivity_factor(14, 2.0, "5m", "optimistic")
    assert conservative < optimistic
    assert five_minute < optimistic
