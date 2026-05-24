from llm_ops.llm_review_schema import enforce_timing_review_schema


def test_head_controller_timing_review_schema_blocks_unsafe_flags():
    row = enforce_timing_review_schema({"live_readiness_opinion": "LIVE_READY", "auto_apply_allowed": True, "live_order_allowed": True})
    assert row["live_readiness_opinion"] == "LIVE_NOT_ALLOWED"
    assert row["auto_apply_allowed"] is False
    assert row["live_order_allowed"] is False
