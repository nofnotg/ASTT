from __future__ import annotations

from capital.capital_policy import validate_capital_policy
from capital.signal_strength_sizer import size_signal_strength


def allocate_full_seed(candidate: dict, policy: dict) -> dict:
    safe_policy = validate_capital_policy(policy)
    sizing = size_signal_strength(candidate, safe_policy)
    max_single = safe_policy["initial_cash_krw"] * safe_policy["max_single_position_pct"]
    allocation = min(sizing["allocation_krw"], max_single)
    return {**sizing, "allocation_krw": allocation, "real_order_enabled": False, "research_mode": True}
