from head_controller.head_controller_evaluation_loop import run_head_controller_evaluation_loop


def test_head_controller_evaluation_loop_never_auto_applies():
    result = run_head_controller_evaluation_loop("docs/reports", "openai")
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
    assert result["live_readiness"] == "LIVE_NOT_ALLOWED"
