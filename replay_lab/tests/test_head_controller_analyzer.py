from head_controller.head_controller_analyzer import analyze_head_controller_context


def test_head_controller_analyzer_detects_enter_zero():
    result = analyze_head_controller_context({"session_summary": {"trade_count": 0}, "entry_discovery": {}})
    assert result["primary_problem"] == "ENTER_0"
    assert result["auto_apply_allowed"] is False
