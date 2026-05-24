from head_controller.llm_json_schema import validate_and_sanitize_llm_output


def test_head_controller_false_positive_review_safety():
    out = validate_and_sanitize_llm_output({"live_readiness_opinion": "LIVE_NOT_ALLOWED", "auto_apply_allowed": True, "live_order_allowed": True, "config_proposals": [{"active": True, "human_approved": True}]})
    assert out["auto_apply_allowed"] is False
    assert out["live_order_allowed"] is False
    assert out["config_proposals"][0]["active"] is False
