from __future__ import annotations

from typing import Any


def conservative_pnl(row: dict[str, Any], fee_slippage_pct: float = 0.20) -> float:
    pnl = float(row.get("pnl_krw", 0.0))
    if pnl > 0.0:
        pnl *= 0.70
    else:
        pnl *= 1.15
    return pnl - abs(float(row.get("position_krw", 0.0))) * fee_slippage_pct / 100.0
