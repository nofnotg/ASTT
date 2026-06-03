from __future__ import annotations

from scenario_telemetry.scenario_genome import build_scenario_genome


def test_v688_scenario_genome_is_paper_locked(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        '{"active_route":"LG_V2_BALANCED_PLUS_DOM_GATE","routes":[{"scenario":"LG_M3_PF0.8_DD8","return_pct":10},{"scenario":"LG_V2_BALANCED_PLUS_DOM_GATE","return_pct":1}]}',
        encoding="utf-8",
    )
    payload = build_scenario_genome(reports)
    assert payload["real_order_enabled"] is False
    assert payload["live_order_allowed"] is False
    assert payload["auto_apply_allowed"] is False
    assert payload["route_state"]["actual_paper_primary_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"
    assert payload["route_state"]["mismatch_warning"] is True
    assert (reports / "latest_v688_scenario_genome_report.html").exists()
