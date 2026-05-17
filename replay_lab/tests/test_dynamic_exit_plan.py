from features.dynamic_exit_plan import build_dynamic_exit_plan


def test_dynamic_exit_plan_runner():
    target = {"target_space_grade": "A", "max_target_space_pct": 4, "target_1": 101, "target_2": 104}
    plan = build_dynamic_exit_plan(100, 99, target, {}, "A")
    assert plan["runner_ratio"] > 0
    assert plan["trailing_stop"]["enabled"]
