from __future__ import annotations


def build_dynamic_exit_plan(entry_price, stop_price, target_space_result, fractal_context, position_grade) -> dict:
    grade = target_space_result.get("target_space_grade", "REJECT")
    max_space = float(target_space_result.get("max_target_space_pct", 0.0))
    if grade == "REJECT" or max_space < 0.8:
        return {"entry_style": "NO_ENTRY", "entry_slices": [], "exit_style": "NO_EXIT", "take_profit_plan": [], "runner_ratio": 0.0, "trailing_stop": {"enabled": False}, "time_stop_minutes": 0, "warnings": ["target_space_too_small"]}
    if max_space < 1.5:
        plan = [{"target": target_space_result["target_1"], "ratio": 1.0, "reason": "target_1_zone_low"}]
        return {"entry_style": "ALL_IN", "entry_slices": [{"ratio": 1.0, "price_rule": "market_or_next_open"}], "exit_style": "FULL_EXIT", "take_profit_plan": plan, "runner_ratio": 0.0, "trailing_stop": {"enabled": False}, "time_stop_minutes": 90, "warnings": []}
    if max_space < 3.0:
        plan = [{"target": target_space_result["target_1"], "ratio": 0.65, "reason": "target_1_zone_low"}, {"target": target_space_result["target_2"], "ratio": 0.35, "reason": "target_2_zone_high"}]
        runner = 0.0
    elif max_space < 6.0:
        plan = [{"target": target_space_result["target_1"], "ratio": 0.4, "reason": "target_1_zone_low"}, {"target": target_space_result["target_2"], "ratio": 0.4, "reason": "target_2_zone_high"}]
        runner = 0.2
    else:
        plan = [{"target": target_space_result["target_1"], "ratio": 0.3, "reason": "target_1_zone_low"}, {"target": target_space_result["target_2"], "ratio": 0.4, "reason": "target_2_zone_high"}]
        runner = 0.3
    return {"entry_style": "ALL_IN" if position_grade in {"A_PLUS", "A"} else "SPLIT_ENTRY", "entry_slices": [{"ratio": 1.0, "price_rule": "market_or_next_open"}], "exit_style": "RUNNER" if runner else "PARTIAL_EXIT", "take_profit_plan": plan, "runner_ratio": runner, "trailing_stop": {"enabled": bool(runner), "mode": "peak_drawdown_pct", "value": 2.5}, "time_stop_minutes": 120, "warnings": []}
