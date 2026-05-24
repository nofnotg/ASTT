import json

from replay_lab.research.llm_strategy_review_v5r3 import run_llm_strategy_review_v5r3


def test_llm_strategy_review_v5r3_records_tokens_and_blocks_live(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    (reports / "latest_market_regime_summary.json").write_text(json.dumps({"dominant_regime": "RISK_ON"}), encoding="utf-8")
    (reports / "latest_setup_candidate_summary.json").write_text(json.dumps({"candidate_count": 1, "by_setup_type": {"PULLBACK_RECLAIM": {"avg_score": 70, "count": 1}}}), encoding="utf-8")
    (reports / "latest_scenario_replay_summary.json").write_text(json.dumps({"scenario_count": 1}), encoding="utf-8")
    (reports / "latest_aggressive_paper_learning_summary.json").write_text(json.dumps({"trade_count": 1, "paper_enter_count": 1, "pnl_evaluable": True, "total_return_pct": 0.1}), encoding="utf-8")

    result = run_llm_strategy_review_v5r3(reports, "off")

    assert result["token_usage"]["completion_tokens"] > 0
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
    assert result["real_order_enabled"] is False
