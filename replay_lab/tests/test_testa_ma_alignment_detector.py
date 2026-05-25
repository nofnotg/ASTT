from ma_strategy.testa_ma_alignment_detector import detect_testa_states


def test_testa_alignment_detects_bull_and_reclaim() -> None:
    states = detect_testa_states({"close": 110, "sma5": 108, "sma25": 104, "sma75": 100, "sma5_slope_pct": 0.3, "sma25_slope_pct": 0.1, "sma75_slope_pct": 0.05})
    assert "TESTA_BULL_ALIGNMENT" in states
    assert "TESTA_RECLAIM_5" in states
