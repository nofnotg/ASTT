from llm_ops.llm_schema_completion_guard import parse_schema_completion


def test_llm_live_call_repair_schema_guard_blocks_missing_json():
    result = parse_schema_completion('{"summary":"ok","live_readiness_opinion":"LIVE_NOT_ALLOWED","auto_apply_allowed":true,"live_order_allowed":true}')
    assert result["schema_valid"] is True
    assert result["parsed"]["auto_apply_allowed"] is False
