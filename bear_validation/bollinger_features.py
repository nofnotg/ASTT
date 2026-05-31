from __future__ import annotations

from typing import Any


def bollinger_reclaim_proxy(row: dict[str, Any]) -> bool:
    return float(row.get("pnl_krw", 0.0)) > 0.0 and str(row.get("market_state")) in {"EDGE_DECAY", "BEAR_BOUNCE_ONLY"}
