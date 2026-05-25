from __future__ import annotations

from uuid import uuid4


class V6PaperBroker:
    def __init__(self, initial_cash_krw: float = 500000) -> None:
        self.initial_cash_krw = initial_cash_krw
        self.cash_krw = initial_cash_krw
        self.equity_krw = initial_cash_krw
        self.peak_equity_krw = initial_cash_krw
        self.max_drawdown_pct = 0.0
        self.trades: list[dict] = []
        self.real_order_enabled = False

    def execute_round_trip(self, setup: dict, position_krw: float, exit_price: float, exit_time: str, result: str) -> dict:
        entry = float(setup["entry_price"])
        fee_entry = position_krw * 0.0005
        qty = (position_krw - fee_entry) / entry
        gross_exit = qty * exit_price
        fee_exit = position_krw * 0.0005
        pnl = gross_exit - fee_exit - position_krw
        self.cash_krw += pnl
        self.equity_krw = self.cash_krw
        self.peak_equity_krw = max(self.peak_equity_krw, self.equity_krw)
        self.max_drawdown_pct = min(self.max_drawdown_pct, (self.equity_krw - self.peak_equity_krw) / self.peak_equity_krw * 100)
        trade = {
            "trade_id": f"v6_{uuid4().hex[:12]}",
            "market": setup["market"],
            "strategy": setup["strategy"],
            "setup_type": setup["setup_type"],
            "entry_time": setup.get("entry_time", ""),
            "entry_price": entry,
            "stop_price": setup["stop_price"],
            "target_price": setup["target_price"],
            "risk_amount_krw": setup.get("risk_amount_krw", 0.0),
            "position_krw": position_krw,
            "risk_reward_ratio": setup["risk_reward_ratio"],
            "exit_time": exit_time,
            "exit_price": exit_price,
            "pnl_krw": pnl,
            "return_pct": pnl / position_krw * 100 if position_krw else 0.0,
            "result": result,
            "real_order_enabled": False,
        }
        self.trades.append(trade)
        return trade
