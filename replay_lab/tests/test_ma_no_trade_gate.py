from ma_strategy.ma_no_trade_gate import should_no_trade


def test_no_trade_gate_uses_bear_or_lost_75_only() -> None:
    assert should_no_trade(["MA_BEAR"])
    assert should_no_trade(["TESTA_LOST_75"])
    assert not should_no_trade(["MA_CHOP"])
