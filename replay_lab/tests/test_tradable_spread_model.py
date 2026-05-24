from tradable_winner.tradable_spread_model import calculate_spread_contraction, calculate_spread_pct


def test_spread_pct_and_contraction():
    assert round(calculate_spread_pct(99, 101), 4) == 2.0
    assert calculate_spread_contraction(0.2, 0.1) == 0.5
