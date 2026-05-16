import pandas as pd

from features.relaxed_exhaustion import detect_drop_event, detect_fear_cooling, detect_low_retest_or_lower_low, evaluate_min_support_context


def _frame() -> pd.DataFrame:
    lows = [100, 99, 98, 97, 96, 95, 95.2, 95.1, 95.0, 95.3, 96, 97]
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=len(lows), freq="min"),
            "open": [value + 0.2 for value in lows],
            "high": [value + 1.0 for value in lows],
            "low": lows,
            "close": [value + 0.5 for value in lows],
            "volume": [100, 120, 200, 300, 500, 450, 350, 300, 250, 230, 220, 210],
            "fear_score": [10, 20, 40, 80, 75, 70, 60, 55, 52, 50, 45, 40],
            "volume_panic": [1, 1.2, 2, 4, 3.5, 3.0, 2.4, 2.1, 2.0, 1.8, 1.5, 1.2],
            "volatility_fear": [1, 1.1, 1.5, 3, 2.5, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.1],
        }
    )


def test_detect_drop_event_and_low_retest():
    frame = _frame()
    drop = detect_drop_event(frame, lookback=12, min_drop_pct=1.0)
    low = detect_low_retest_or_lower_low(frame, tolerance_pct=0.5)
    assert drop["has_drop_event"]
    assert drop["drop_pct"] >= 1.0
    assert low["pattern"] in {"LOWER_LOW", "LOW_RETEST"}


def test_detect_fear_cooling_accepts_any_cooling_leg():
    frame = _frame()
    result = detect_fear_cooling(frame, cooling_ratio=0.95)
    assert result["has_fear_cooling"]
    assert result["cooling_type"] in {"FEAR_SCORE", "VOLUME_PANIC", "VOLATILITY_FEAR", "MIXED"}


def test_evaluate_min_support_context_accepts_one_support_source():
    frame = _frame()
    result = evaluate_min_support_context(
        frame,
        body_zone_result={"body_zone_score": 35, "distance_to_support_pct": 0.4, "target_space_pct": 0.8},
        trendline_result={"trendline_score": 0},
        ma_context_result={"ma30": 98, "ma_context_score": 20},
        bollinger_result={"middle_band": 98},
    )
    assert result["has_min_support"]
    assert "BODY_ZONE" in result["support_sources"]
