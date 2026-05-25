from __future__ import annotations


def calculate_risk_reward(entry_price: float, stop_price: float, target_price: float) -> float:
    risk = max(float(entry_price) - float(stop_price), 0.0)
    reward = max(float(target_price) - float(entry_price), 0.0)
    return float(reward / risk) if risk else 0.0
