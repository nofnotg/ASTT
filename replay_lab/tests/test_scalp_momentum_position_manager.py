from execution.scalp_momentum_position_manager import build_scalp_momentum_exit_plan, manage_scalp_momentum_position


def test_position_manager_has_ladders_and_keeps_stop_loss():
    plan = build_scalp_momentum_exit_plan("TRADABLE_MOMENTUM")
    assert [row["pct"] for row in plan["exit_plan"]] == [0.5, 0.3, 0.2]
    assert plan["stop_loss_removable"] is False
    assert manage_scalp_momentum_position({}, {"hold_seconds": 999}, "TRADABLE_SCALP")["decision"] == "TIME_STOP"
