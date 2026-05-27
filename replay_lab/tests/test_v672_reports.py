from __future__ import annotations

import json
from pathlib import Path

from replay_lab.feedback.v672_btcdom_index_reports_html import V672BTCDOMIndexDataQualityHTML


def test_v672_data_quality_html_builds_korean_report(tmp_path: Path):
    (tmp_path / "latest_v672_btcdom_index_data_quality_summary.json").write_text(
        json.dumps(
            {
                "files": {"1d": {"exists": True, "rows": 1, "start": "s", "end": "e", "close_min": 1600, "close_max": 1700, "source_type": "BTCDOM_INDEX_PROXY", "quality": "GOOD"}},
                "source_type": "BTCDOM_INDEX_PROXY",
                "is_percentage": False,
                "common_coverage_start": "s",
                "common_coverage_end": "e",
                "fake_data_generated": False,
            }
        ),
        encoding="utf-8",
    )
    result = V672BTCDOMIndexDataQualityHTML(str(tmp_path)).build()
    text = Path(result["html"]).read_text(encoding="utf-8")
    assert "BTCDOM Index 데이터 품질" in text
    assert "BTCDOM_INDEX_PROXY" in text
