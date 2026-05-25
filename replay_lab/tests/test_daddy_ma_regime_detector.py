from ma_strategy.daddy_ma_regime_detector import detect_daddy_ma_states


def test_daddy_ma_detects_bull_squeeze_breakout() -> None:
    states = detect_daddy_ma_states({"close": 105, "sma20": 104, "sma200": 103, "sma20_slope_pct": 0.2, "sma200_slope_pct": 0.1})
    assert "MA_BULL" in states
    assert "MA_SQUEEZE_BREAKOUT" in states
