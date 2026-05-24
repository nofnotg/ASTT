from timing_lab.event_type_quality_scorer import _event_type


def test_event_type_quality_scorer_extracts_event_type():
    assert _event_type("KRWBTC_MARKET_RANK_SURGE_1") == "MARKET_RANK_SURGE"
