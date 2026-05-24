from head_controller.head_controller_safety_guard import enforce_head_controller_safety


def test_head_controller_safety_blocks_live_and_auto_apply():
    out = enforce_head_controller_safety({"live_readiness_opinion": "MICRO_LIVE_READY", "auto_apply_allowed": True, "config_proposals": [{"active": True, "human_approved": True}]})
    assert out["live_readiness_opinion"] == "LIVE_NOT_ALLOWED"
    assert out["auto_apply_allowed"] is False
    assert out["config_proposals"][0]["active"] is False
