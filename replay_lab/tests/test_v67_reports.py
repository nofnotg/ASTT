from __future__ import annotations

import json

from replay_lab.feedback.v67_global_btcd_reports_html import V67GlobalBTCDDataQualityHTML


def test_v67_data_quality_report_html(tmp_path):
    (tmp_path / "latest_v67_global_btcd_data_quality_summary.json").write_text(json.dumps({"data_sources": {}, "full_period_validation_possible": False, "reason": "GLOBAL_BTCD_DATA_REQUIRED"}), encoding="utf-8")
    result = V67GlobalBTCDDataQualityHTML(str(tmp_path)).build()
    assert result["html"].endswith(".html")
    assert "Global BTC Dominance" in (tmp_path / "latest_v67_global_btcd_data_quality_report.html").read_text(encoding="utf-8")
