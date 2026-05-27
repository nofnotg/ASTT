from __future__ import annotations

from analysis.v672_btcdom_index_rejector import build_v672_rejection_report


def test_v672_rejector_separates_kept_and_rejected():
    report = build_v672_rejection_report(
        {
            "scenarios": [
                {"scenario": "CONTROL_EXISTING", "decision": "BASELINE"},
                {"scenario": "A", "decision": "BTCDOM_INDEX_FILTER_VALIDATED"},
                {"scenario": "B", "decision": "BTCDOM_INDEX_FILTER_REJECTED"},
            ]
        }
    )
    assert report["kept_candidates"][0]["scenario"] == "A"
    assert report["rejected_scenarios"][0]["scenario"] == "B"
