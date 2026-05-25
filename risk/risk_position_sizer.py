from __future__ import annotations


def size_position(
    account_cash_krw: float = 500000,
    entry_price: float = 0.0,
    stop_price: float = 0.0,
    risk_per_trade_pct: float = 1.0,
    max_position_pct: float = 1.0,
    min_stop_distance_pct: float = 0.8,
) -> dict:
    if entry_price <= 0 or stop_price <= 0 or stop_price >= entry_price:
        return {"position_krw": 0.0, "risk_amount_krw": 0.0, "stop_distance_pct": 0.0, "sizing_valid": False, "reason": "INVALID_STOP"}
    raw_stop_distance_pct = (entry_price - stop_price) / entry_price * 100
    stop_distance_pct = max(raw_stop_distance_pct, min_stop_distance_pct)
    risk_amount = account_cash_krw * risk_per_trade_pct / 100
    position_krw = risk_amount / (stop_distance_pct / 100)
    position_krw = min(position_krw, account_cash_krw * max_position_pct)
    return {
        "position_krw": float(position_krw),
        "risk_amount_krw": float(risk_amount),
        "stop_distance_pct": float(stop_distance_pct),
        "raw_stop_distance_pct": float(raw_stop_distance_pct),
        "sizing_valid": position_krw >= 5000,
        "reason": None if position_krw >= 5000 else "BELOW_MIN_ORDER",
    }
