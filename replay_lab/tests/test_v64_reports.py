from __future__ import annotations

import json
from pathlib import Path

from replay_lab.feedback.v64_causal_defense_html_report import V64CausalDefenseHTMLReport


def test_v64_html_report_builds_korean_report(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v64_causal_defense_summary.json").write_text(
        json.dumps({"scenarios": [{"scenario": "BASELINE", "capital": {"final_equity_krw": 500000, "total_return_pct": 0, "max_drawdown_pct": 0, "profit_factor": 1, "trade_count": 1, "return_to_mdd_ratio": 0}}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = V64CausalDefenseHTMLReport().build(str(reports))
    html = Path(result["html"]).read_text(encoding="utf-8")

    assert "정답지" in html
    assert "\ufffd" not in html
