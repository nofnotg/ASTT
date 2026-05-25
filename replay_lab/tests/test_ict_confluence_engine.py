from ict_strategy.ict_confluence_engine import build_ict_confluences


def test_ict_confluence_engine_scores_overlap():
    result = build_ict_confluences("KRW-BTC", [{"zone_type": "BULLISH_FVG", "timeframe": "1h", "zone_low": 100, "zone_high": 110, "quality_score": 60}], [{"zone_type": "BULLISH_ORDER_BLOCK", "zone_low": 105, "zone_high": 115, "quality_score": 70}], [])
    assert result[0]["confluence_type"] == "FVG_OB_OVERLAP"
