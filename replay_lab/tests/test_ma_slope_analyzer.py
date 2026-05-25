from ma_strategy.ma_slope_analyzer import is_down_slope, is_up_slope, slope_pct


def test_slope_pct_and_direction_helpers() -> None:
    assert round(slope_pct(110, 100) or 0, 2) == 10.0
    assert is_up_slope(0.2)
    assert is_down_slope(-0.2)
