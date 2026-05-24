from features.wait_path_features import compute_wait_path_features


def test_wait_path_classifies_missed_win_research_only():
    candidate = {"candidate_id": "c1", "market": "KRW-BTC", "candidate_source": "VWAP_RECLAIM", "candidate_time_ms": 1000, "reference_price": 100.0}
    snapshots = [{"market": "KRW-BTC", "timestamp_ms": 1000, "last_price": 100.0}, {"market": "KRW-BTC", "timestamp_ms": 30000, "last_price": 100.4}]
    row = compute_wait_path_features(candidate, snapshots)
    assert row["wait_classification"] == "MISSED_WIN"
    assert row["research_only"] is True
    assert row["included_in_pnl"] is False
