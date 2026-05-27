from __future__ import annotations

from analysis.v67_global_btcd_rejector import build_v67_rejection_report


def test_v67_rejector_separates_candidates():
    report = build_v67_rejection_report({"scenarios": [{"scenario": "CONTROL_EXISTING", "decision": "BASELINE"}, {"scenario": "A", "decision": "GLOBAL_BTCD_DATA_REQUIRED"}, {"scenario": "B", "decision": "GLOBAL_BTCD_RELATIVE_STRENGTH_CANDIDATE"}]})
    assert report["rejected_scenarios"][0]["scenario"] == "A"
    assert report["kept_candidates"][0]["scenario"] == "B"
