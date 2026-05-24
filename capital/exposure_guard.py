from __future__ import annotations


def check_exposure_guard(account: dict, policy: dict, proposed_order_krw: float) -> dict:
    if policy.get("real_order_enabled") is True:
        return {"allowed": False, "reason": "REAL_ORDER_BLOCKED"}
    if account.get("open_positions", 0) >= policy.get("max_open_positions", 1):
        return {"allowed": False, "reason": "MAX_OPEN_POSITIONS_REACHED"}
    equity = float(account.get("equity_krw", policy.get("initial_cash_krw", 500000)))
    exposure = float(account.get("exposure_krw", 0.0)) + float(proposed_order_krw)
    if equity and exposure / equity > policy.get("max_total_exposure_pct", 1.0):
        return {"allowed": False, "reason": "MAX_TOTAL_EXPOSURE_REACHED"}
    if account.get("session_return_pct", 0.0) <= policy.get("session_stop_loss_pct", -1.0):
        return {"allowed": False, "reason": "SESSION_STOP_LOSS_REACHED"}
    if account.get("daily_return_pct", 0.0) <= policy.get("daily_stop_loss_pct", -2.0):
        return {"allowed": False, "reason": "DAILY_STOP_LOSS_REACHED"}
    if account.get("head_controller_risk_level") == "HIGH":
        return {"allowed": False, "reason": "HEAD_CONTROLLER_HIGH_RISK"}
    return {"allowed": True, "reason": "OK"}
