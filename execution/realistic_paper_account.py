from __future__ import annotations

from uuid import uuid4


class RealisticPaperAccount:
    def __init__(self, initial_cash_krw: float = 500000, fixed_order_krw: float = 10000):
        self.initial_cash_krw = initial_cash_krw
        self.cash_krw = initial_cash_krw
        self.equity_krw = initial_cash_krw
        self.fixed_order_krw = fixed_order_krw
        self.realized_pnl_krw = 0.0
        self.unrealized_pnl_krw = 0.0
        self.open_positions: dict[str, dict] = {}
        self.closed_positions: list[dict] = []
        self.peak_equity_krw = initial_cash_krw
        self.max_drawdown_pct = 0.0

    def can_open_position(self, order_krw: float) -> bool:
        return len(self.open_positions) < 1 and self.cash_krw >= order_krw

    def open_position(self, order: dict, fill: dict) -> dict:
        order_krw = float(order.get("order_krw", self.fixed_order_krw))
        if not self.can_open_position(order_krw):
            raise RuntimeError("paper account cannot open position")
        position_id = f"paper_{uuid4().hex[:12]}"
        qty = (order_krw - fill.get("fee_krw", 0.0)) / fill["fill_price"]
        position = {**order, "position_id": position_id, "entry_price": fill["fill_price"], "quantity": qty, "order_krw": order_krw, "entry_fee_krw": fill.get("fee_krw", 0.0), "status": "OPEN"}
        self.cash_krw -= order_krw
        self.open_positions[position_id] = position
        self.mark_to_market({position["market"]: fill["fill_price"]})
        return position

    def close_position(self, position_id: str, fill: dict, reason: str) -> dict:
        position = self.open_positions.pop(position_id)
        gross = position["quantity"] * fill["fill_price"]
        exit_fee = fill.get("fee_krw", 0.0)
        cash_back = gross - exit_fee
        pnl = cash_back - position["order_krw"]
        closed = {**position, "exit_price": fill["fill_price"], "exit_fee_krw": exit_fee, "exit_reason": reason, "pnl_krw": pnl, "pnl_pct": pnl / position["order_krw"] * 100, "status": "CLOSED"}
        self.cash_krw += cash_back
        self.realized_pnl_krw += pnl
        self.closed_positions.append(closed)
        self.mark_to_market({})
        return closed

    def mark_to_market(self, market_prices: dict) -> dict:
        unrealized = 0.0
        for position in self.open_positions.values():
            price = float(market_prices.get(position["market"], position["entry_price"]))
            unrealized += position["quantity"] * price - position["order_krw"]
        self.unrealized_pnl_krw = unrealized
        self.equity_krw = self.cash_krw + sum(position["order_krw"] for position in self.open_positions.values()) + unrealized
        self.peak_equity_krw = max(self.peak_equity_krw, self.equity_krw)
        self.max_drawdown_pct = min(self.max_drawdown_pct, (self.equity_krw - self.peak_equity_krw) / self.peak_equity_krw * 100 if self.peak_equity_krw else 0.0)
        return self.summary()

    def summary(self) -> dict:
        wins = [p for p in self.closed_positions if p.get("pnl_krw", 0.0) > 0]
        losses = [p for p in self.closed_positions if p.get("pnl_krw", 0.0) <= 0]
        return {"cash_krw": self.cash_krw, "equity_krw": self.equity_krw, "realized_pnl_krw": self.realized_pnl_krw, "unrealized_pnl_krw": self.unrealized_pnl_krw, "open_positions": len(self.open_positions), "closed_positions": len(self.closed_positions), "trade_count": len(self.closed_positions), "win_count": len(wins), "loss_count": len(losses), "max_drawdown_pct": self.max_drawdown_pct}
