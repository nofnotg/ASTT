from replay_lab.research.head_controller_v5r2_review import run_head_controller_v5r2_review


def test_head_controller_v5r2_review_forces_safety_flags():
    result = run_head_controller_v5r2_review("docs/reports", "off")
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
