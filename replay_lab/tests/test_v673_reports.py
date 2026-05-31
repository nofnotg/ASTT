from __future__ import annotations

import json
from pathlib import Path

from replay_lab.feedback.v673_reports_html import V673AgentMatrixHTML


def test_v673_agent_matrix_html_builds(tmp_path: Path):
    (tmp_path / "latest_v673_agent_matrix_summary.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "scenario": "POLICY_BLEND_CONTROL",
                        "final_equity_krw": 500000,
                        "total_return_pct": 0,
                        "mdd_pct": 0,
                        "profit_factor": 0,
                        "trade_count": 0,
                        "return_mdd_ratio": 0,
                        "decision": "BASELINE",
                    }
                ],
                "lookahead_audit": {"checked_trades": 0, "fail": 0},
            }
        ),
        encoding="utf-8",
    )

    out = V673AgentMatrixHTML(str(tmp_path)).build()

    assert Path(out["html"]).exists()
    assert "No live orders" in Path(out["html"]).read_text(encoding="utf-8")
