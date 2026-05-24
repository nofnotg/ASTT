from __future__ import annotations


class AccountEquityTracker:
    def __init__(self, initial_cash_krw: float = 500000):
        self.initial_cash_krw = float(initial_cash_krw)
        self.curve = [{"step": 0, "equity_krw": self.initial_cash_krw, "return_pct": 0.0, "drawdown_pct": 0.0}]
        self.peak = self.initial_cash_krw
        self.max_drawdown_pct = 0.0

    def add(self, equity_krw: float, step: int | None = None) -> dict:
        equity = float(equity_krw)
        self.peak = max(self.peak, equity)
        drawdown = (equity - self.peak) / self.peak * 100 if self.peak else 0.0
        self.max_drawdown_pct = min(self.max_drawdown_pct, drawdown)
        row = {
            "step": len(self.curve) if step is None else step,
            "equity_krw": equity,
            "return_pct": (equity - self.initial_cash_krw) / self.initial_cash_krw * 100 if self.initial_cash_krw else 0.0,
            "drawdown_pct": drawdown,
        }
        self.curve.append(row)
        return row

    def summary(self) -> dict:
        last = self.curve[-1]
        return {"equity_curve": self.curve, "final_equity_krw": last["equity_krw"], "max_drawdown_pct": self.max_drawdown_pct}
