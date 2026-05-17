from __future__ import annotations


class CompoundingPortfolio:
    def __init__(self, initial_equity_krw: float):
        self.initial_equity_krw = float(initial_equity_krw)
        self.current_equity_krw = float(initial_equity_krw)
        self.peak_equity_krw = float(initial_equity_krw)
        self.max_drawdown_pct = 0.0
        self.history: list[dict] = []

    def apply_trade_result(self, trade_result: dict) -> dict:
        before = self.current_equity_krw
        allocation = float(trade_result.get("allocation_pct", 0.0))
        position_size = before * allocation
        pnl_pct = float(trade_result.get("net_pnl_pct", trade_result.get("realized_pnl_pct", 0.0)))
        pnl = position_size * pnl_pct / 100
        self.current_equity_krw += pnl
        self.peak_equity_krw = max(self.peak_equity_krw, self.current_equity_krw)
        dd = (self.current_equity_krw - self.peak_equity_krw) / self.peak_equity_krw * 100 if self.peak_equity_krw else 0.0
        self.max_drawdown_pct = min(self.max_drawdown_pct, dd)
        row = {"trade_id": trade_result.get("trade_id", str(len(self.history) + 1)), "before_equity_krw": before, "allocation_pct": allocation, "position_size_krw": position_size, "net_pnl_pct": pnl_pct, "trade_pnl_krw": pnl, "after_equity_krw": self.current_equity_krw, "equity_return_pct": (self.current_equity_krw - self.initial_equity_krw) / self.initial_equity_krw * 100 if self.initial_equity_krw else 0.0, "max_drawdown_pct": self.max_drawdown_pct}
        self.history.append(row)
        return row
