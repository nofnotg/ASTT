from ma_strategy.ma_policy_router import route_policy


def test_policy_router_blocks_lost_75_and_routes_plan_b() -> None:
    blocked = route_policy({"plan": "PLAN_A_ICT_FAT_TAIL"}, ["TESTA_LOST_75"], 50, "NORMAL")
    assert blocked["multiplier_scale"] == 0.0
    routed = route_policy({"plan": "PLAN_B_COMBINED_CONTEXT"}, ["MA_BULL"], 80, "NORMAL")
    assert routed["policy"] == "BALANCED_GROWTH"
