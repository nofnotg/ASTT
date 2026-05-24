from features.redesigned_candidate_sources import (
    detect_orderflow_surge_candidate,
    detect_volume_range_breakout_candidate,
    detect_vwap_reclaim_with_volume_candidate,
)


SNAPSHOT = {
    "market": "KRW-ABC",
    "timestamp_ms": 1,
    "last_price": 100,
    "previous_high_distance_pct": 0.1,
    "range_position_pct": 80,
    "volume_burst_ratio_10s_vs_60s": 2.0,
    "trade_count_acceleration": 2.0,
    "spread_pct": 0.1,
    "buy_trade_ratio_10s": 0.6,
    "orderbook_imbalance": 0.2,
    "vwap_distance_pct": 0.1,
}


def test_redesigned_candidates_generate_schema():
    assert detect_volume_range_breakout_candidate(SNAPSHOT)["real_order_enabled"] is False
    assert detect_orderflow_surge_candidate(SNAPSHOT)["research_mode"] is True
    assert detect_vwap_reclaim_with_volume_candidate(SNAPSHOT)["candidate_source"] == "VWAP_RECLAIM_WITH_VOLUME"


def test_redesigned_candidate_returns_none_when_conditions_fail():
    weak = {**SNAPSHOT, "spread_pct": 1.0}
    assert detect_volume_range_breakout_candidate(weak) is None
