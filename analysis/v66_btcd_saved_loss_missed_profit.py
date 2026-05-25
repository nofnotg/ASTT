from __future__ import annotations


def net_effect(saved_loss_krw: float, missed_profit_krw: float) -> float:
    return float(saved_loss_krw) - float(missed_profit_krw)

