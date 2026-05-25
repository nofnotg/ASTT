from __future__ import annotations

import json

from replay_lab.research.v64_policy_blend_analysis import build_v64_policy_blend_analysis


def test_v64_policy_blend_analysis_compares_rolling_and_balanced(tmp_path):
    reports = tmp_path / "docs/reports"
    reports.mkdir(parents=True)
    journal = []
    for idx in range(30):
        pnl = -1000.0 if idx % 3 else 2000.0
        journal.append(
            {
                "trade_id": f"t{idx}",
                "entry_time": f"2025-01-{idx + 1:02d} 00:00:00",
                "exit_time": f"2025-01-{idx + 1:02d} 01:00:00",
                "feature_cutoff_time": f"2025-01-{idx + 1:02d} 00:00:00",
                "market": "KRW-TEST",
                "plan": "PLAN_B_COMBINED_CONTEXT",
                "strategy": "COMBINED_VOLUME_ICT",
                "setup_type": "DADDY_CONTEXT+FVG_OB_OVERLAP",
                "pnl_krw": pnl,
            }
        )
    (reports / "latest_true_walk_forward_summary.json").write_text(
        json.dumps({"capital": {"initial_cash_krw": 500000}, "journal": journal}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_v64_policy_blend_analysis(str(reports))

    assert summary["real_order_enabled"] is False
    assert summary["live_order_allowed"] is False
    assert "rolling_vs_balanced" in summary
    assert summary["policy_activity"]["ROLLING_EDGE_THROTTLE"]["actions"]["ENTER"] == 30
    assert (reports / "latest_v64_policy_blend_analysis_summary.json").exists()
    html = (reports / "latest_v64_policy_blend_analysis_report.html").read_text(encoding="utf-8")
    assert "Rolling Edge" in html
    assert "Balanced Growth" in html
