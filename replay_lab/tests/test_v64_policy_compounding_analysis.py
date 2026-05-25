from __future__ import annotations

import json

from replay_lab.research.v64_policy_compounding_analysis import build_v64_policy_compounding_analysis


def test_policy_compounding_recomputes_position_from_policy_equity(tmp_path):
    reports = tmp_path / "docs/reports"
    reports.mkdir(parents=True)
    journal = []
    for idx in range(25):
        journal.append(
            {
                "trade_id": f"t{idx}",
                "date": f"2025-01-{idx + 1:02d}",
                "entry_time": f"2025-01-{idx + 1:02d} 00:00:00",
                "exit_time": f"2025-01-{idx + 1:02d} 01:00:00",
                "feature_cutoff_time": f"2025-01-{idx + 1:02d} 00:00:00",
                "market": "KRW-TEST",
                "plan": "PLAN_A_ICT_FAT_TAIL",
                "strategy": "ICT_FVG_OB_SWEEP",
                "setup_type": "FVG_OB_OVERLAP",
                "entry_price": 100.0,
                "exit_price": 102.0 if idx % 2 == 0 else 98.0,
                "stop_price": 95.0,
                "target_price": 110.0,
            }
        )
    (reports / "latest_true_walk_forward_summary.json").write_text(
        json.dumps({"capital": {"initial_cash_krw": 500000}, "journal": journal}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_v64_policy_compounding_analysis(str(reports))

    assert summary["real_order_enabled"] is False
    assert summary["live_order_allowed"] is False
    assert len(summary["scenarios"]) == 2
    assert summary["period_returns"]["ROLLING_EDGE_THROTTLE"]["weekly"]
    assert summary["period_returns"]["BALANCED_GROWTH"]["monthly"]
    assert "rolling_vs_balanced" in summary
    assert (reports / "latest_v64_policy_compounding_summary.json").exists()
    html = (reports / "latest_v64_policy_compounding_report.html").read_text(encoding="utf-8")
    assert "복리 재산정" in html
    assert "연별 수익률" in html
