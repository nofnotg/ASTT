from __future__ import annotations


def default_capital_policy(initial_cash_krw: float = 500000) -> dict:
    return {
        "initial_cash_krw": float(initial_cash_krw),
        "max_total_exposure_pct": 1.0,
        "max_single_position_pct": 1.0,
        "max_open_positions": 1,
        "daily_stop_loss_pct": -2.0,
        "session_stop_loss_pct": -1.0,
        "real_order_enabled": False,
        "research_mode": True,
    }


def validate_capital_policy(policy: dict) -> dict:
    if policy.get("real_order_enabled") is True:
        raise ValueError("real_order_enabled_must_remain_false")
    safe = {**default_capital_policy(policy.get("initial_cash_krw", 500000)), **policy}
    safe["real_order_enabled"] = False
    safe["research_mode"] = True
    return safe
