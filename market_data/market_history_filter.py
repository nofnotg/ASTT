from __future__ import annotations


def has_sufficient_history(actual_months: float, requested_months: int) -> bool:
    return actual_months >= requested_months * 0.8
