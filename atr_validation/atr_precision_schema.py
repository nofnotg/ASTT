from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ATRAuditConfig:
    atr_period: int = 14
    atr_multiplier: float = 2.0
    atr_timeframe: str = "1h"
    fee_slippage_pct: float = 0.20
