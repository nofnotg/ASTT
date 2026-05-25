from ma_strategy.sma_calculator import rolling_sma, simple_moving_average


def test_simple_moving_average_requires_full_window() -> None:
    assert simple_moving_average([1, 2], 3) is None
    assert simple_moving_average([1, 2, 3], 3) == 2


def test_rolling_sma_outputs_none_until_window_ready() -> None:
    assert rolling_sma([1, 2, 3, 4], 3) == [None, None, 2, 3]
