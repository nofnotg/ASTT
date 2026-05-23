from __future__ import annotations


def compute_micro_target_space(candidate: dict, snapshot: dict, fee_pct: float = 0.05, slippage_pct: float = 0.05, min_reward_to_cost: float = 5.0) -> dict:
    target = float(candidate.get("expected_target_pct", 0.0))
    stop = float(candidate.get("expected_stop_pct", 0.0))
    cost = fee_pct * 2 + slippage_pct
    reward_to_cost = target / cost if cost else 999.0
    tradable = reward_to_cost >= min_reward_to_cost
    return {"expected_target_pct": target, "expected_stop_pct": stop, "estimated_total_cost_pct": cost, "reward_to_cost": reward_to_cost, "tradable": tradable, "reject_reason": None if tradable else "TARGET_TOO_SMALL"}
