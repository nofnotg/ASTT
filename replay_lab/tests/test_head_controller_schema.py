from head_controller.head_controller_schema import build_controller_output


def test_head_controller_schema_defaults_safe():
    out = build_controller_output("ENTER_0", [], [])
    assert out["live_readiness_opinion"] == "LIVE_NOT_ALLOWED"
    assert out["auto_apply_allowed"] is False
