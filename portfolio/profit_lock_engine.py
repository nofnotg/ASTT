from __future__ import annotations

from collections import defaultdict


class ProfitLockEngine:
    def __init__(self, initial_cash_krw: float) -> None:
        self.initial_cash_krw = float(initial_cash_krw)
        self.month_start_equity: dict[str, float] = {}

    def monthly_multiplier_cap(self, month: str, current_equity: float) -> tuple[float, list[str]]:
        self.month_start_equity.setdefault(month, float(current_equity))
        start = self.month_start_equity[month]
        if start <= 0:
            return 1.5, []
        month_return = (float(current_equity) / start - 1.0) * 100
        if month_return >= 10.0:
            return 0.5, ["PROFIT_LOCK_MONTHLY_10"]
        total_return = (float(current_equity) / self.initial_cash_krw - 1.0) * 100
        if total_return >= 100.0:
            return 1.0, ["PROFIT_LOCK_ORIGINAL_CAPITAL"]
        if total_return >= 50.0:
            return 1.25, ["PROFIT_LOCK_RETURN_50"]
        return 1.5, []
