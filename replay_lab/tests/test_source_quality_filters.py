from features.source_quality_filters import source_quality_pass


def test_source_quality_filters_reject_wide_spread():
    result = source_quality_pass({"spread_pct": 0.5, "bid_ask_size_ratio": 2.0})
    assert result["quality_pass"] is False
    assert "SPREAD_TOO_WIDE" in result["reject_reasons"]
