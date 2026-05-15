from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VirtualPortfolio:
    cash_krw: float

    def total_asset(self, position_value_krw: float = 0.0) -> float:
        return self.cash_krw + position_value_krw

