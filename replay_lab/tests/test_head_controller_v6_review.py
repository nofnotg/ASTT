import json

from replay_lab.research.head_controller_v6_review import run_head_controller_v6_review


def test_head_controller_v6_review_blocks_live_and_picks_strategy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    for name, strategy, expectancy in [
        ("latest_v6_daddy_strategy_summary.json", "DADDY_VOLUME_NECKLINE", -1),
        ("latest_v6_ict_strategy_summary.json", "ICT_FVG_OB_SWEEP", 1),
        ("latest_v6_combined_strategy_summary.json", "COMBINED_VOLUME_ICT", 0.5),
    ]:
        (reports / name).write_text(json.dumps({"strategy": strategy, "trade_count": 1, "expectancy_pct": expectancy}), encoding="utf-8")
    (reports / "latest_v6_weekly_performance_summary.json").write_text(json.dumps({}), encoding="utf-8")
    result = run_head_controller_v6_review(reports, "off")
    assert result["best_strategy"] == "ICT_FVG_OB_SWEEP"
    assert result["live_order_allowed"] is False
