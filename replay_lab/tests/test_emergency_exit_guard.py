from execution.emergency_exit_guard import check_emergency_exit


def test_emergency_exit_guard_detects_btc_and_orderbook_shock():
    result = check_emergency_exit(
        {"price_change_5s_pct": -0.4},
        {"micro_state": "STABLE"},
        {"spread_pct": 0.5, "orderbook_imbalance": -0.8},
    )

    assert result["emergency"] is True
    assert "BTC_MICRO_SHOCK" in result["reason"]
    assert result["severity"] == "HIGH"
