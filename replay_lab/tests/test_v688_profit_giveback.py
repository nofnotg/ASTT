from __future__ import annotations

from scenario_telemetry.scenario_profit_giveback import build_profit_giveback_analysis


def test_v688_profit_giveback_calculates_ratios(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        '{"active_route":"LG_V2_BALANCED_PLUS_DOM_GATE","daily_equity":{"LG_V2_BALANCED_PLUS_DOM_GATE":[{"period":"2026-01-01","pnl_krw":1000},{"period":"2026-01-02","pnl_krw":-800}]}}',
        encoding="utf-8",
    )
    payload = build_profit_giveback_analysis(reports_dir=reports, data_dir=tmp_path / "data")
    assert payload["rows"][0]["giveback_ratio_1d"] == 0.8
    assert payload["live_order_allowed"] is False
