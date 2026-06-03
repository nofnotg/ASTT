from __future__ import annotations

import json
from pathlib import Path

from analysis.v691_vwap_pressure_lab import run_v691_vwap_pressure_feature_lab
from vwap_pressure.vpf_pressure_score import classify_vpf
from vwap_pressure.vwap_calculator import attach_vwap_features, daily_anchored_vwap, rolling_vwap


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
            ],
        },
    )
    _write(
        reports / "latest_v688_profit_giveback_summary.json",
        {"rows": [{"scenario_id": "LG_M3_PF0.8_DD8", "profit_date": "2026-02-02", "profit_day_pnl": 10000, "giveback_ratio_1d": 0.6, "giveback_ratio_3d": 0.7}]},
    )
    _write(reports / "latest_v688_missed_opportunity_summary.json", {"candidate_count": 12, "rows": [{"date": "2026-06-02"}]})
    _write(reports / "latest_v690_failure_signature_summary.json", {"failure_signatures": [{"failure_type": "PROFIT_GIVEBACK_1D_3D"}]})


def test_vwap_calculator_uses_only_current_and_past_rows() -> None:
    rows = [
        {"timestamp": "2026-01-01T09:00:00+09:00", "high": 10, "low": 10, "close": 10, "volume": 1},
        {"timestamp": "2026-01-01T10:00:00+09:00", "high": 20, "low": 20, "close": 20, "volume": 1},
        {"timestamp": "2026-01-01T11:00:00+09:00", "high": 1000, "low": 1000, "close": 1000, "volume": 1},
    ]

    assert rolling_vwap(rows, 2)[:2] == [10.0, 15.0]
    assert daily_anchored_vwap(rows)[:2] == [10.0, 15.0]
    enriched = attach_vwap_features(rows, rolling_4h=2, rolling_24h=2)
    assert enriched[1]["daily_anchored_vwap"] == 15.0
    assert enriched[1]["rolling_vwap_24h"] == 15.0


def test_vpf_classifier_marks_grey_as_no_trade_pressure() -> None:
    row = classify_vpf(
        {
            "vwap_distance_pct": 0.05,
            "volume_zscore": 0.2,
            "candle_body_ratio": 0.1,
            "close_location_in_range": 0.50,
            "chop_cross_count": 4,
        }
    )

    assert row["vpf_state"] == "GREY"
    assert row["vpf_reason"] == "estimated_pressure_from_ohlcv_not_orderflow"


def test_v691_loop_adds_drawdown_shadow_candidate_without_live_actions(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _seed_reports(reports)

    payload = run_v691_vwap_pressure_feature_lab(reports)

    assert payload["decision"] == "VWAP_SHADOW_CANDIDATE"
    assert "LG_M3_VWAP_PRESSURE_INTEGRATED_V1" in payload["vwap_shadow_candidates"]
    assert "LG_M3_VWAP_PRESSURE_INTEGRATED_V1" in payload["drawdown_shadow_candidates"]
    assert payload["real_order_enabled"] is False
    assert payload["live_order_allowed"] is False
    assert payload["auto_apply_allowed"] is False
    assert payload["active_change_applied"] is False
    assert (reports / "latest_v691_drawdown_reduction_report.html").exists()
    assert (reports / "latest_v691_vwap_decision_report.html").exists()
