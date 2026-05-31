from __future__ import annotations

import json
from pathlib import Path

from replay_lab.feedback.integrated_investment_report_html import IntegratedInvestmentReportHTML


def test_integrated_investment_report_builds_period_records(tmp_path: Path):
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    summary = {
        "capital": {"final_equity_krw": 520000, "total_return_pct": 4.0, "max_drawdown_pct": -2.0, "trade_count": 2},
        "journal": [
            {"date": "2026-01-01", "entry_time": "2026-01-01 09:00:00", "equity_before": 500000, "equity_after": 510000, "pnl_krw": 10000},
            {"date": "2026-01-02", "entry_time": "2026-01-02 09:00:00", "equity_before": 510000, "equity_after": 520000, "pnl_krw": 10000},
        ],
    }
    (reports / "latest_v62_full_investment_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (reports / "latest_v673_agent_matrix_summary.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {"scenario": "POLICY_BLEND_CONTROL", "final_equity_krw": 520000, "total_return_pct": 4.0, "mdd_pct": -2.0, "trade_count": 2},
                    {"scenario": "SCENARIO_AGENT_ROUTER_V1", "final_equity_krw": 530000, "total_return_pct": 6.0, "mdd_pct": -1.0, "trade_count": 2},
                ],
                "period_records": {
                    "SCENARIO_AGENT_ROUTER_V1": {
                        "monthly": [{"period": "2026-01", "start_equity_krw": 500000, "end_equity_krw": 530000, "pnl_krw": 30000, "return_pct": 6.0, "mdd_pct": -1.0, "trade_count": 2}],
                        "weekly": [{"period": "2026-W01", "start_date": "2026-01-01", "end_date": "2026-01-02", "start_equity_krw": 500000, "end_equity_krw": 530000, "pnl_krw": 30000, "return_pct": 6.0, "mdd_pct": -1.0, "trade_count": 2}],
                        "daily": [{"period": "2026-01-01", "date": "2026-01-01", "start_equity_krw": 500000, "end_equity_krw": 530000, "pnl_krw": 30000, "return_pct": 6.0, "mdd_pct": -1.0, "trade_count": 2}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "latest_v673_scenario_router_summary.json").write_text(
        json.dumps({"scenarios": [{"scenario": "SCENARIO_AGENT_ROUTER_V1", "final_equity_krw": 530000, "total_return_pct": 6.0, "mdd_pct": -1.0}], "market_state_pnl": []}),
        encoding="utf-8",
    )

    result = IntegratedInvestmentReportHTML().build(str(reports))
    html = Path(result["html"]).read_text(encoding="utf-8")
    integrated = json.loads((reports / "latest_integrated_investment_summary.json").read_text(encoding="utf-8"))

    assert "월 단위 투자 기록" in html
    assert "시나리오 선택" in html
    assert "시나리오별 월 변화량 비교" in html
    assert "data-period" in html
    assert "Forward Shadow Paper" in html
    assert len(integrated["daily_rows"]) == 2
    assert len(integrated["weekly_rows"]) == 1
    assert len(integrated["monthly_rows"]) == 1
    assert len(integrated["dominance"]["scenario_period_records"]["SCENARIO_AGENT_ROUTER_V1"]["monthly"]) == 1
    assert len(integrated["dominance"]["scenario_monthly_comparison"]) == 1
    assert (reports / "latest_v62_daily_summary.json").exists()
