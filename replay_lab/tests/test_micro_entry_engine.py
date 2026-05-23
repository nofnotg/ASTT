from execution.micro_entry_engine import decide_micro_entry


def test_micro_entry_engine_enters_on_good_micro_conditions():
    result = decide_micro_entry(
        {"setup_pass": True, "reference_price": 100},
        {"micro_state": "ACCELERATING", "buy_trade_ratio_5s": 0.7, "price_change_5s_pct": 0.1},
        {"liquidity_state": "GOOD", "spread_pct": 0.1, "best_ask_price": 100.1},
        {"btc_shock": False},
    )

    assert result["entry_decision"] == "ENTER"
    assert result["entry_price"] == 100.1


def test_micro_entry_engine_cancels_on_wide_spread():
    result = decide_micro_entry(
        {"setup_pass": True, "reference_price": 100},
        {"micro_state": "ACCELERATING", "buy_trade_ratio_5s": 0.7, "price_change_5s_pct": 0.1},
        {"liquidity_state": "WIDE_SPREAD", "spread_pct": 0.4},
        {"btc_shock": False},
    )

    assert result["entry_decision"] == "CANCEL"
