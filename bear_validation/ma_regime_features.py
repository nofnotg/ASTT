from __future__ import annotations

from typing import Any


def ma_regime_risk(row: dict[str, Any]) -> bool:
    return str(row.get("btc_trend")) == "DOWN" or str(row.get("market_state")) in {"BEAR_DEFENSE", "LOCKDOWN"}
