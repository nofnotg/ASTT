import json

from replay_lab.research.v6_weekly_paper_simulation import run_v6_weekly_paper_simulation


def test_v6_weekly_paper_simulation_reads_strategy_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    sample = {"trades": [{"exit_time": "2026-01-01", "pnl_krw": 1000}]}
    for name in ["latest_v6_daddy_strategy_summary.json", "latest_v6_ict_strategy_summary.json", "latest_v6_combined_strategy_summary.json"]:
        (reports / name).write_text(json.dumps(sample), encoding="utf-8")
    result = run_v6_weekly_paper_simulation()
    assert result["weekly_trade_count"] == 3
