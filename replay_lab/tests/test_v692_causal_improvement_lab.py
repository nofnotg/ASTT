from __future__ import annotations

import json
from pathlib import Path

from causal_improvement.v692_lab import (
    generate_v692_train_based_improvement_candidates,
    run_v692_historical_to_2026_causal_improvement_lab,
    run_v692_vwap_proxy_vs_real,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_reports(tmp_path: Path) -> Path:
    reports = tmp_path / "reports"
    reports.mkdir()
    _write_json(
        reports / "latest_v683_backfill_20260101_summary.json",
        {
            "routes": [
                {"scenario": "LG_V2_BALANCED_PLUS_DOM_GATE", "return_pct": 3.22, "mdd_pct": -18.23, "profit_factor": 1.05, "trade_count": 254},
                {"scenario": "LG_M3_PF0.8_DD8", "return_pct": 3.53, "mdd_pct": -17.98, "profit_factor": 1.055, "trade_count": 254},
                {"scenario": "BASE_ROLLING", "return_pct": 4.0, "mdd_pct": -21.0, "profit_factor": 1.04, "trade_count": 260},
            ]
        },
    )
    _write_json(
        reports / "latest_v689_scenario_decision_summary.json",
        {
            "current_rows": [],
            "long_term_rows": [
                {"scenario": "RELATIVE_STRENGTH_BTCD", "return_pct": 205.0, "mdd_pct": -19.0, "profit_factor": 1.26, "trade_count": 1348}
            ],
        },
    )
    _write_json(
        reports / "latest_v688_profit_giveback_summary.json",
        {"rows": [{"scenario_id": "LG_M3_PF0.8_DD8", "profit_day_pnl": 12000}]},
    )
    _write_json(reports / "latest_v688_missed_opportunity_summary.json", {"candidate_count": 12, "missed_profit_1d": 3.2})
    _write_json(
        reports / "latest_v691_2026_vwap_scenario_backtest_summary.json",
        {
            "rows": [
                {"scenario": "LG_M3_VWAP_GREY_FILTER_V1", "return_pct": 3.8, "mdd_pct": -16.9},
                {"scenario": "LG_M3_VWAP_PRESSURE_INTEGRATED_V1", "return_pct": 4.4, "mdd_pct": -15.4},
            ]
        },
    )
    return reports


def test_v692_lab_keeps_hindsight_repair_research_only(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    result = run_v692_historical_to_2026_causal_improvement_lab(reports)

    assert result["decision"] == "SHADOW_CANDIDATE_READY"
    assert "TRAIN_LG_M3_RS_BTCD_OVERLAY_V1" in result["causal_shadow_candidates"]
    assert "HINDSIGHT_2026_VWAP_PRESSURE_INTEGRATED_REPAIR" in result["hindsight_repair_research_only"]
    assert result["live_order_allowed"] is False
    assert result["active_change_applied"] is False
    assert (reports / "latest_v692_causal_decision_summary.json").exists()
    assert (reports / "latest_v692_historical_to_2026_causal_improvement_lab_report.html").exists()


def test_v692_candidate_guard_flags_train_vs_hindsight(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    result = generate_v692_train_based_improvement_candidates(reports)

    train_rows = [row for row in result["candidates"] if row["hindsight_risk"] == "LOW_TRAIN_ONLY"]
    hindsight_rows = [row for row in result["candidates"] if row["hindsight_risk"] == "HIGH_2026_USED"]
    assert train_rows
    assert all(row["eligible_for_operation"] is True for row in train_rows)
    assert hindsight_rows == [
        {
            "candidate": "HINDSIGHT_2026_VWAP_PRESSURE_INTEGRATED_REPAIR",
            "base": "LG_M3_PF0.8_DD8",
            "derived_from": "2026 weakness and V6.9.1 proxy result",
            "rule": "2026 결과를 보고 만든 VWAP integrated repair",
            "hindsight_risk": "HIGH_2026_USED",
            "train_evidence": "2026_USED",
            "eligible_for_operation": False,
            "test_status": "HINDSIGHT_REPAIR_RESEARCH_ONLY",
        }
    ]


def test_v692_vwap_proxy_is_not_operational_evidence(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    result = run_v692_vwap_proxy_vs_real(reports)

    integrated = next(row for row in result["rows"] if row["vwap_scenario"] == "LG_M3_VWAP_PRESSURE_INTEGRATED_V1")
    assert integrated["real_replay_return_pct"] is None
    assert integrated["decision"] == "VWAP_PROXY_NOT_OPERATIONAL_EVIDENCE"
    assert (reports / "latest_v692_vwap_full_period_real_safety_summary.json").exists()
