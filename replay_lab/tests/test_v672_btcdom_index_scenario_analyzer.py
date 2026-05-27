from __future__ import annotations

from analysis.v672_btcdom_index_scenario_analyzer import _data_required_summary


def test_v672_data_required_summary_is_safe():
    row = _data_required_summary("BTCDOM_INDEX_RELATIVE_STRENGTH_FILTER")
    assert row["trade_count"] == 0
    assert row["decision"] == "BTCDOM_INDEX_DATA_REQUIRED"
