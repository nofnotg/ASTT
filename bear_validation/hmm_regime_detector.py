from __future__ import annotations

from typing import Any


def hmm_regime_proxy(row: dict[str, Any]) -> str:
    state = str(row.get("market_state") or "SIDEWAYS")
    if state in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"}:
        return "RISK_OFF"
    if state == "EDGE_DECAY":
        return "HIGH_VOL_DOWN"
    if state in {"BULL_ATTACK", "ALT_FRIENDLY"}:
        return "LOW_VOL_UP"
    return "SIDEWAYS"
