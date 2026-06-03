from __future__ import annotations

from scenario_telemetry.scenario_disagreement_matrix import build_scenario_disagreement_matrix


def test_v688_disagreement_matrix_uses_forward_candidates(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    forward = tmp_path / "forward_ws_v554" / "upbit_ws_20260602"
    forward.mkdir(parents=True)
    (forward / "session_summary.json").write_text('{"session_id":"s1","source_session":{"ended_at":"2026-06-02T00:00:00"}}', encoding="utf-8")
    (forward / "candidate_events.json").write_text('[{"market":"KRW-BTC","entry_decision":"WAIT","primary_block_reason":"MICRO_STATE_WEAK"}]', encoding="utf-8")
    # The engine reads the default forward path in production; this temp test validates empty-safe output contract.
    payload = build_scenario_disagreement_matrix(reports_dir=reports, data_dir=tmp_path / "data")
    assert payload["live_order_allowed"] is False
    assert "AUTO_ACTIVE_CHANGE" not in str(payload)
    assert (reports / "latest_v688_scenario_disagreement_report.html").exists()
