from __future__ import annotations

from strategy_engine.v61_setup_filter_policy import setup_decision


def test_v61_setup_filter_policy_keeps_positive_setup():
    assert setup_decision(0.5, 3) == "KEEP"
    assert setup_decision(-2, 3) == "DISABLE"
