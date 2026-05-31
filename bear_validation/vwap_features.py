from __future__ import annotations

from typing import Any


def vwap_failure_proxy(row: dict[str, Any]) -> bool:
    return str(row.get("market_state")) in {"EDGE_DECAY", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE"}
