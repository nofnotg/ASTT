from ma_strategy.ma_overextension_detector import is_overextended


def test_overextension_helper() -> None:
    assert is_overextended(["MA_OVEREXTENDED"])
    assert not is_overextended(["MA_BULL"])
