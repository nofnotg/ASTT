from __future__ import annotations

from typing import Any


def optimistic_pnl(row: dict[str, Any], fee_slippage_pct: float = 0.05) -> float:
    pnl = float(row.get("pnl_krw", 0.0))
    return pnl * 0.95 - abs(float(row.get("position_krw", 0.0))) * fee_slippage_pct / 100.0
