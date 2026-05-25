from __future__ import annotations

from strategy_engine.v61_strategy_decision import decide_strategy


def test_v61_strategy_decision_disables_negative_expectancy():
    decision = decide_strategy({"trade_count": 3, "expectancy_pct": -2, "max_drawdown_pct": -3})
    assert decision == "STRATEGY_DISABLE"
