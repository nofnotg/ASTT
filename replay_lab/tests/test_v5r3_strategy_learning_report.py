import json

from replay_lab.feedback.v5r3_strategy_learning_html_report import V5R3StrategyLearningHTMLReport


def test_v5r3_strategy_learning_report_outputs_json_md_html(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    for name, payload in {
        "latest_market_regime_summary.json": {"dominant_regime": "RISK_ON"},
        "latest_setup_candidate_summary.json": {"candidate_count": 1, "by_setup_type": {}},
        "latest_scenario_replay_summary.json": {"scenario_count": 1, "by_scenario_type": {}},
        "latest_aggressive_paper_learning_summary.json": {"paper_enter_count": 1, "trade_count": 1, "pnl_evaluable": True},
        "latest_llm_strategy_review_summary.json": {"live_readiness_opinion": "PAPER_MORE_REQUIRED", "token_usage": {"completion_tokens": 10}},
    }.items():
        (reports / name).write_text(json.dumps(payload), encoding="utf-8")

    result = V5R3StrategyLearningHTMLReport().build(reports)

    assert (reports / "latest_v5r3_strategy_learning_summary.json").exists()
    assert (reports / "latest_v5r3_strategy_learning_report.md").exists()
    assert (reports / "latest_v5r3_strategy_learning_report.html").exists()
    assert result["html"].endswith(".html")
