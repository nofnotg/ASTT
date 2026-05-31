from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ATRReplayConfig:
    atr_period: int = 14
    atr_multiplier: float = 2.0
    timeframe: str = "1m"
    fill_model: str = "conservative"
    trailing_update_mode: str = "close_confirmed_next_bar"
    fee_pct: float = 0.05
    slippage_pct: float = 0.10

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
