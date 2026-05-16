from features.structure_reversal import classify_structure_reversal


def test_structure_reversal_types():
    result = classify_structure_reversal({"weekly": {"weekly_bias_score": 70}, "daily": {"support_held": True}, "h4": {"ma_reclaimed": True}, "rs_flip": {}, "trendline": {}, "body_zone": {}})
    assert result["strategy_type"] == "TREND_CONTINUATION_PULLBACK"
    result = classify_structure_reversal({"weekly": {}, "daily": {"support_held": True}, "h4": {}, "rs_flip": {"has_rs_flip": True, "rs_flip_score": 80}, "trendline": {}, "body_zone": {}})
    assert result["strategy_type"] == "FAILED_BREAKDOWN_RECLAIM"
