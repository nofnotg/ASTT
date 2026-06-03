from __future__ import annotations

from scenario_telemetry.scenario_daily_stats import build_scenario_telemetry


def test_v688_scenario_telemetry_outputs_daily_weekly_monthly(tmp_path) -> None:
    reports = tmp_path / "reports"
    data = tmp_path / "data"
    reports.mkdir()
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        '{"active_route":"LG_V2_BALANCED_PLUS_DOM_GATE","initial_cash_krw":500000,"daily_equity":{"LG_V2_BALANCED_PLUS_DOM_GATE":[{"period":"2026-01-01","pnl_krw":1000,"return_pct":0.2,"trade_count":1},{"period":"2026-01-02","pnl_krw":-500,"return_pct":-0.1,"trade_count":1}]},"routes":[]}',
        encoding="utf-8",
    )
    payload = build_scenario_telemetry(reports_dir=reports, data_dir=data)
    assert payload["daily"]["row_count"] >= 2
    assert payload["weekly"]["rows"]
    assert payload["monthly"]["rows"]
    assert payload["daily"]["real_order_enabled"] is False
    assert (reports / "latest_v688_scenario_telemetry_report.html").exists()
