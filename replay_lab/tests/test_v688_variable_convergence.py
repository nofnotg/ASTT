from __future__ import annotations

from scenario_telemetry.scenario_variable_convergence import build_variable_convergence_analysis


def test_v688_variable_convergence_marks_sample_count(tmp_path) -> None:
    reports = tmp_path / "reports"
    journal = tmp_path / "data" / "journal"
    reports.mkdir()
    journal.mkdir(parents=True)
    (journal / "paper_decisions.jsonl").write_text('{"pf20":1.2,"dominance_risk":false}\n', encoding="utf-8")
    payload = build_variable_convergence_analysis(reports_dir=reports, data_dir=tmp_path / "data")
    assert payload["winning_common_variables"][0]["sample_count"] >= 0
    assert "causation" in payload["caution"]
