from live_capture.high_volatility_session_planner import plan_high_volatility_session


def test_high_volatility_session_plans_known_windows():
    assert "08:50" in plan_high_volatility_session("MORNING_0900")["recommended_window"]
    assert "22:20" in plan_high_volatility_session("US_OPEN_2230")["recommended_window"]
    assert plan_high_volatility_session("RANDOM_CONTROL")["real_order_enabled"] is False
