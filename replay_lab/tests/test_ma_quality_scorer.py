from ma_strategy.ma_quality_scorer import score_ma_quality


def test_ma_quality_rewards_alignment_and_penalizes_lost_75() -> None:
    high, _ = score_ma_quality(["MA_BULL", "TESTA_BULL_ALIGNMENT", "MA_SQUEEZE_BREAKOUT"])
    low, _ = score_ma_quality(["MA_CHOP", "TESTA_LOST_75"])
    assert high > 80
    assert low < 20
