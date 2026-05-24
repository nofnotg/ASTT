from replay_lab.research.head_controller_tradable_winner_review_v5510 import run_head_controller_tradable_winner_review_v5510


def test_head_controller_tradable_review_is_guarded(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_tradable_winner_mining_summary.json").write_text('{"tradable_winner_count":0}', encoding="utf-8")
    (reports / "latest_tradable_source_forward_summary.json").write_text('{"ENTER":0}', encoding="utf-8")
    result = run_head_controller_tradable_winner_review_v5510(str(reports), "off")
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
