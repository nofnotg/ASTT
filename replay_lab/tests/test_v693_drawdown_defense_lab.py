from __future__ import annotations

import json
from pathlib import Path

from causal_improvement.v692_lab import run_v692_historical_to_2026_causal_improvement_lab
from drawdown_defense.v693_lab import (
    generate_v693_defense_scenario_candidates,
    run_v693_2026_drawdown_autopsy,
    run_v693_2026_defense_forward_test,
    run_v693_drawdown_defense_autopsy_lab,
    run_v693_loss_type_classification,
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
            ]
        },
    )
    _write_json(reports / "latest_v689_scenario_decision_summary.json", {"current_rows": [], "long_term_rows": []})
    _write_json(reports / "latest_v688_profit_giveback_summary.json", {"rows": [{"profit_day_pnl": 10000}]})
    _write_json(reports / "latest_v688_missed_opportunity_summary.json", {"candidate_count": 5})
    _write_json(
        reports / "latest_v691_2026_vwap_scenario_backtest_summary.json",
        {"rows": [{"scenario": "LG_M3_VWAP_GREY_FILTER_V1", "return_pct": 3.8, "mdd_pct": -16.9}]},
    )
    run_v692_historical_to_2026_causal_improvement_lab(reports)
    return reports


def test_v693_autopsy_extracts_loss_events_and_months(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    payload = run_v693_2026_drawdown_autopsy(reports)

    assert payload["loss_event_count"] > 0
    assert payload["monthly"]
    assert payload["loss_events"][0]["failure_type"]
    assert payload["loss_events"][0]["preventable"] in {"PREVENTABLE", "PARTIALLY_PREVENTABLE", "NOT_PREVENTABLE", "INSUFFICIENT_DATA"}
    assert payload["live_order_allowed"] is False


def test_v693_loss_types_and_candidates_are_train_guarded(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    loss_types = run_v693_loss_type_classification(reports)
    candidates = generate_v693_defense_scenario_candidates(reports)

    assert loss_types["rows"]
    assert any(row["suggested_defense"].startswith("DEF_") for row in loss_types["rows"])
    hindsight = next(row for row in candidates["rows"] if row["decision"] == "HINDSIGHT_REPAIR_RESEARCH_ONLY")
    assert hindsight["eligible_for_operation"] is False
    assert all(row["eligible_for_operation"] for row in candidates["rows"] if row["decision"] == "READY_FOR_DEFENSE_FORWARD_TEST")


def test_v693_forward_decision_and_safety_flags(tmp_path: Path) -> None:
    reports = _seed_reports(tmp_path)
    forward = run_v693_2026_defense_forward_test(reports)
    loop = run_v693_drawdown_defense_autopsy_lab(reports)

    assert any(row["defense_efficiency"] > 1.0 for row in forward["rows"])
    assert "DEF_INTEGRATED_BALANCED_V1" in loop["defense_shadow_candidates"]
    assert "HINDSIGHT_2026_CUSTOM_REPAIR_RESEARCH_ONLY" in loop["hindsight_repair_research_only"]
    assert loop["real_order_enabled"] is False
    assert loop["active_change_applied"] is False
    assert (reports / "latest_v693_defense_decision_summary.json").exists()
