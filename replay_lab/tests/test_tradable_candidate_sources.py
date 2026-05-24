from features.tradable_candidate_sources import detect_tradable_candidate


def _snapshot(**overrides):
    row = {"market": "KRW-AAA", "timestamp_ms": 1, "last_price": 100, "tradable_prefilter_pass": True, "effective_return_pct": 0.6, "estimated_total_cost_pct": 0.1, "spread_pct": 0.1, "depth_3_level_krw": 2_000_000, "volume_burst_60s_vs_600s": 1.5, "price_change_60s_pct": 0.2, "buy_trade_ratio_60s": 0.6, "orderbook_imbalance": 0.1, "vwap_distance_pct": 0.1}
    row.update(overrides)
    return row


def test_tradable_candidate_sources_generate_and_reject():
    assert detect_tradable_candidate(_snapshot(), "TRADABLE_VOLUME_BREAKOUT")
    assert detect_tradable_candidate(_snapshot(), "TRADABLE_ORDERFLOW_EXPANSION")
    assert detect_tradable_candidate(_snapshot(range_compression_score=0.8), "TRADABLE_COMPRESSION_BREAK")
    assert detect_tradable_candidate(_snapshot(spread_pct=0.5), "TRADABLE_VOLUME_BREAKOUT") is None
