from ma_strategy.ma_squeeze_detector import is_squeeze_breakout


def test_squeeze_breakout_helper() -> None:
    assert is_squeeze_breakout(["MA_SQUEEZE_BREAKOUT"])
    assert not is_squeeze_breakout(["MA_SQUEEZE"])
