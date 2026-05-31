from __future__ import annotations

from typing import Any


def rsi_recovery_proxy(row: dict[str, Any]) -> bool:
    return bool(row.get("bear_bounce_v3_candidate")) or str(row.get("market_state")) == "BEAR_BOUNCE_ONLY"
