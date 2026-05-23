from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from features.micro_cost_model import apply_micro_cost_model


@dataclass
class ForwardPaperPosition:
    position_id: str
    market: str
    entry_time: str
    entry_price: float
    order_krw: float
    target_price: float
    stop_price: float
    max_hold_seconds: int = 120
    status: str = "OPEN"
    exit_time: str | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    pnl_pct: float = 0.0
    pnl_krw: float = 0.0

    def close(self, exit_price: float, reason: str, exit_time: str | None = None) -> dict:
        self.status = "CLOSED"
        self.exit_time = exit_time or datetime.utcnow().isoformat()
        self.exit_price = exit_price
        self.exit_reason = reason
        self.pnl_pct = (exit_price - self.entry_price) / self.entry_price * 100 if self.entry_price else 0.0
        self.pnl_krw = self.order_krw * self.pnl_pct / 100
        return self.to_result()

    def to_result(self) -> dict:
        base = self.__dict__.copy()
        for scenario in ["gross", "fee_only", "realistic_1"]:
            costed = apply_micro_cost_model({"realized_pnl_pct": self.pnl_pct}, scenario)
            base[f"{scenario}_pnl_pct"] = costed["net_pnl_pct"]
            base[f"{scenario}_pnl_krw"] = self.order_krw * costed["net_pnl_pct"] / 100
        return base
