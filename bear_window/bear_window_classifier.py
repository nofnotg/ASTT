from __future__ import annotations

from typing import Any


def classify_window(window: dict[str, Any]) -> str:
    trigger = str(window.get("trigger_reason", ""))
    state = str(window.get("market_state", ""))
    dom = str(window.get("dominance_regime", ""))
    ret = float(window.get("monthly_return_pct", 0.0))
    mdd = float(window.get("HWM_drawdown", 0.0))
    if state in {"RISK_OFF_ALT_WEAK", "LOCKDOWN"}:
        return "RISK_OFF_WINDOW"
    if state == "BTC_LED_MARKET" or "RISING" in dom or "SPIKE" in dom:
        return "BTC_LED_ALT_WEAK_WINDOW"
    if mdd <= -8.0:
        return "DRAWDOWN_WINDOW"
    if ret > 0.0 and "HWM_DRAWDOWN" in trigger:
        return "RECOVERY_WINDOW"
    return "EDGE_DECAY_WINDOW"
