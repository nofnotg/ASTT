from risk.stop_target_planner import plan_stop_target


def test_stop_target_planner_requires_valid_entry():
    result = plan_stop_target(100, zone_low=97)
    assert result["valid"] is True
    assert result["target_price"] > 100
