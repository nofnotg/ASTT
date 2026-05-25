from ma_strategy.ma_chop_detector import is_ma_chop


def test_ma_chop_detects_daddy_or_testa_chop() -> None:
    assert is_ma_chop(["MA_CHOP"])
    assert is_ma_chop(["TESTA_CHOP"])
    assert not is_ma_chop(["MA_BULL"])
