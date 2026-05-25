from __future__ import annotations

from replay_lab.research.head_controller_v61_review import run_head_controller_v61_review


def test_head_controller_v61_review_forces_safety_flags(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v61_final_decision_summary.json").write_text('{"forward_candidates":["ICT"],"disabled_strategies":["DADDY"]}', encoding="utf-8")
    (reports / "latest_v61_strategy_robustness_summary.json").write_text('{"strategies":[{"strategy":"ICT","trade_count":1,"expectancy_pct":1},{"strategy":"DADDY","trade_count":1,"expectancy_pct":-1}]}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = run_head_controller_v61_review(str(reports), "openai")
    assert result["live_order_allowed"] is False
    assert result["real_order_enabled"] is False
    assert result["best_strategy"] == "ICT"
