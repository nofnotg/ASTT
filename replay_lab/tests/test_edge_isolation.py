from __future__ import annotations

from features.edge_isolation import STRATEGY_IDS, build_edge_signal


def test_edge_isolation_three_strategy_schema():
    seed = {"market": "KRW-BTC", "signal_time_kst": "2026-01-01T00:00:00", "entry_price": 100, "zone_stop": 99, "daily_structure_score": 70, "h4_flow_score": 65, "v5_score": 80}
    for strategy_id in STRATEGY_IDS:
        signal = build_edge_signal(seed, strategy_id)
        assert signal["strategy_id"] == strategy_id
        assert signal["entry_allowed"] is True
        assert {"daily", "h4", "zone", "trigger", "risk"} <= set(signal["components"])
