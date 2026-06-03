from __future__ import annotations

import json

from scenario_telemetry.v689_scenario_decision import build_v689_scenario_decision


def test_v689_scenario_decision_filters_low_sample_srr(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v66_btcd_scenario_comparison_summary.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {"scenario": "CONTROL_EXISTING", "total_return_pct": 100, "mdd_pct": -20, "profit_factor": 1.2, "trade_count": 1000, "decision": "BASELINE"},
                    {"scenario": "RELATIVE_STRENGTH_BTCD", "total_return_pct": 110, "mdd_pct": -18, "profit_factor": 1.3, "trade_count": 1000, "decision": "BEAR_ROUTER_CANDIDATE"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (reports / "latest_v681_compounding_router_summary.json").write_text(json.dumps({"scenarios": []}), encoding="utf-8")
    (reports / "latest_integrated_investment_summary.json").write_text(json.dumps({"monthly_rows": [{}, {}]}), encoding="utf-8")
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        json.dumps(
            {
                "active_route": "LG_V2_BALANCED_PLUS_DOM_GATE",
                "routes": [
                    {"scenario": "LG_V2_BALANCED_PLUS_DOM_GATE", "return_pct": 3.2, "mdd_pct": -18.2, "profit_factor": 1.05, "trade_count": 254, "final_equity_krw": 516100},
                    {"scenario": "LG_M3_PF0.8_DD8", "return_pct": 3.5, "mdd_pct": -17.9, "profit_factor": 1.06, "trade_count": 254, "final_equity_krw": 517600},
                ],
                "monthly_returns": {"LG_M3_PF0.8_DD8": [{"period": "2026-05", "pnl_krw": 2300, "return_pct": 0.45, "trade_count": 46}]},
                "weekly_returns": {"LG_M3_PF0.8_DD8": [{"period": "2026-W21", "pnl_krw": 100, "return_pct": 0.02, "trade_count": 4}]},
                "daily_equity": {"LG_M3_PF0.8_DD8": [{"period": "2026-05-24", "pnl_krw": 50, "return_pct": 0.01, "trade_count": 1, "end_equity_krw": 517600}]},
            }
        ),
        encoding="utf-8",
    )
    (reports / "latest_v688_surge_rr_scenario_summary.json").write_text(
        json.dumps({"routes": [{"scenario": "SRR_AGGRESSIVE_WF", "return_pct": 0.1, "mdd_pct": 0, "profit_factor": 99, "trade_count": 3}], "monthly_returns": {}}),
        encoding="utf-8",
    )

    payload = build_v689_scenario_decision(reports)

    assert payload["operating_summary"]["recommended_primary_route"] == "LG_M3_PF0.8_DD8"
    assert payload["operating_summary"]["long_term_best"]["scenario"] == "RELATIVE_STRENGTH_BTCD"
    assert payload["active_change_applied"] is False
    assert payload["live_order_allowed"] is False
