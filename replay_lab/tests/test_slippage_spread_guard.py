from execution.slippage_spread_guard import estimate_micro_execution_cost


def test_slippage_spread_guard_marks_costly_trade_untradable():
    result = estimate_micro_execution_cost(100, 100.5, 100.0, 10000, expected_target_pct=0.6)

    assert result["spread_pct"] > 0.25
    assert result["tradable"] is False


def test_slippage_spread_guard_uses_orderbook_units():
    result = estimate_micro_execution_cost(100, 100.02, 100.0, 10000, [{"ask_price": 100.02, "ask_size": 200}], expected_target_pct=1.0)

    assert result["estimated_slippage_pct"] == 0
    assert result["tradable"] is True
