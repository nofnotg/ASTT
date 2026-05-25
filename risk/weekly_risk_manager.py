from __future__ import annotations


class WeeklyRiskManager:
    def __init__(self, initial_cash_krw: float = 500000, max_daily_risk_pct: float = 3.0, max_weekly_risk_pct: float = 8.0) -> None:
        self.initial_cash_krw = initial_cash_krw
        self.max_daily_loss = -initial_cash_krw * max_daily_risk_pct / 100
        self.max_weekly_loss = -initial_cash_krw * max_weekly_risk_pct / 100
        self.daily_pnl: dict[str, float] = {}
        self.weekly_pnl: dict[str, float] = {}

    def can_enter(self, day_key: str, week_key: str) -> bool:
        return self.daily_pnl.get(day_key, 0.0) > self.max_daily_loss and self.weekly_pnl.get(week_key, 0.0) > self.max_weekly_loss

    def record(self, day_key: str, week_key: str, pnl_krw: float) -> None:
        self.daily_pnl[day_key] = self.daily_pnl.get(day_key, 0.0) + pnl_krw
        self.weekly_pnl[week_key] = self.weekly_pnl.get(week_key, 0.0) + pnl_krw
