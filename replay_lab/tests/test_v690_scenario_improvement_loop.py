from __future__ import annotations

import json
from pathlib import Path

from scenario_improvement.v690_loop import (
    run_v690_scenario_improvement_loop,
    run_v690_improvement_decision_engine,
)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _seed_reports(reports: Path) -> None:
    reports.mkdir(parents=True)
    _write(
        reports / "latest_v683_backfill_20260101_summary.json",
        {
            "active_route": "LG_V2_BALANCED_PLUS_DOM_GATE",
            "routes": [
                {"scenario": "LG_V2_BALANCED_PLUS_DOM_GATE", "final_equity_krw": 516100, "return_pct": 3.22, "mdd_pct": -18.23, "profit_factor": 1.05, "trade_count": 254},
                {"scenario": "LG_M3_PF0.8_DD8", "final_equity_krw": 517671, "return_pct": 3.53, "mdd_pct": -17.98, "profit_factor": 1.055, "trade_count": 254},
                {"scenario": "BASE_ROLLING", "final_equity_krw": 520000, "return_pct": 4.0, "mdd_pct": -21.0, "profit_factor": 1.04, "trade_count": 260},
            ],
            "daily_equity": {"LG_M3_PF0.8_DD8": [{"period": "2026-02-01", "pnl_krw": -1000}]},
            "monthly_returns": {
                "LG_M3_PF0.8_DD8": [{"period": "2026-02", "return_pct": -1.0, "mdd_pct": -5.0}],
                "LG_V2_BALANCED_PLUS_DOM_GATE": [{"period": "2026-02", "return_pct": -2.0, "mdd_pct": -6.0}],
            },
        },
    )
    _write(
        reports / "latest_v689_scenario_decision_summary.json",
        {
            "operating_summary": {
                "long_term_best": {"scenario": "RELATIVE_STRENGTH_BTCD", "return_pct": 205.0, "mdd_pct": -19.0, "profit_factor": 1.26, "trade_count": 1348}
            },
            "long_term_rows": [{"scenario": "RELATIVE_STRENGTH_BTCD", "return_pct": 205.0, "mdd_pct": -19.0, "profit_factor": 1.26, "trade_count": 1348}],
            "current_rows": [],
        },
    )
    _write(reports / "latest_v688_scenario_monthly_summary.json", {"rows": []})
    _write(
        reports / "latest_v688_profit_giveback_summary.json",
        {"rows": [{"scenario_id": "LG_M3_PF0.8_DD8", "profit_date": "2026-02-02", "profit_day_pnl": 10000, "giveback_ratio_1d": 0.6, "giveback_ratio_3d": 0.7}]},
    )
    _write(reports / "latest_v688_missed_opportunity_summary.json", {"candidate_count": 12, "false_block_rate": 0.2, "valid_block_rate": 0.8, "rows": [{"date": "2026-06-02"}]})
    _write(reports / "latest_v688_scenario_disagreement_summary.json", {"rows": [{"disagreement_type": "ALL_SKIP_BUT_OUTCOME_UNKNOWN"}]})
    _write(reports / "latest_v688_variable_convergence_summary.json", {"winning_common_variables": []})
    _write(reports / "latest_v685_bear_window_performance_summary.json", {})
    _write(reports / "latest_v684_loss_guard_indicator_lab_summary.json", {})
    _write(reports / "latest_v684_indicator_effectiveness_summary.json", {})


def test_v690_loop_creates_shadow_candidate_without_live_actions(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _seed_reports(reports)

    payload = run_v690_scenario_improvement_loop(reports)

    assert payload["decision"] == "SHADOW_CANDIDATE_READY"
    assert "LG_M3_RS_BTCD_OVERLAY_V1" in payload["shadow_candidates"]
    assert payload["real_order_enabled"] is False
    assert payload["live_order_allowed"] is False
    assert payload["auto_apply_allowed"] is False
    assert payload["active_change_applied"] is False
    assert (reports / "latest_v690_2026_improvement_backtest_report.html").exists()
    assert (reports / "latest_v690_improvement_llm_review_report.html").exists()
    assert (reports / "astt_report_dashboard.html").exists()


def test_v690_decision_never_auto_applies_active_route(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _seed_reports(reports)

    decision = run_v690_improvement_decision_engine(reports)

    assert decision["active_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"
    assert decision["active_route_change_applied"] is False
    assert decision["llm_active_change_applied"] is False
    assert decision["manual_review_required"] is True
