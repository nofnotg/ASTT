from __future__ import annotations

from btcd.btcdom_index_alignment import btcdom_lookahead_pass


def test_btcdom_alignment_rejects_future_feature_time():
    assert btcdom_lookahead_pass({"lookahead_check": "PASS", "btcdom_feature_time_1d": "2023-01-01T00:00:00Z"}, "2023-01-02T00:00:00Z")
    assert not btcdom_lookahead_pass({"lookahead_check": "PASS", "btcdom_feature_time_1d": "2023-01-03T00:00:00Z"}, "2023-01-02T00:00:00Z")
