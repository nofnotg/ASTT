from __future__ import annotations

from typing import Any


def neutral_pnl(row: dict[str, Any], fee_slippage_pct: float = 0.12) -> float:
    pnl = float(row.get("pnl_krw", 0.0))
    return pnl * 0.85 - abs(float(row.get("position_krw", 0.0))) * fee_slippage_pct / 100.0
