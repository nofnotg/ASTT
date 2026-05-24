from head_controller.llm_fallback_analyzer import fallback_head_controller_analysis


def test_llm_fallback_analyzer_safe():
    out = fallback_head_controller_analysis({"session_summary": {"trade_count": 0}, "artifact_guard": {"allowed": True}}, "off")
    assert out["fallback_used"] is True
    assert out["auto_apply_allowed"] is False
    assert out["live_order_allowed"] is False
