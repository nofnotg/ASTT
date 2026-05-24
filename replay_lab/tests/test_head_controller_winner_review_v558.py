from replay_lab.research.head_controller_winner_pattern_review_v558 import run_head_controller_winner_review_v558


def test_head_controller_winner_review_safety_flags():
    result = run_head_controller_winner_review_v558("docs/reports", "off")
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
    assert result["live_readiness_opinion"] in {"LIVE_NOT_ALLOWED", "PAPER_MORE_REQUIRED"}
