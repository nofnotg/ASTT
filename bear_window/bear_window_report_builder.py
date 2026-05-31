from __future__ import annotations

from typing import Any


def router_decision(active: dict[str, Any], router: dict[str, Any]) -> str:
    router_return = float(router.get("bear_window_return", router.get("bear_window_return_pct", -999.0)))
    active_return = float(active.get("bear_window_return", active.get("bear_window_return_pct", -999.0)))
    router_mdd = float(router.get("bear_window_mdd", router.get("bear_window_mdd_pct", -999.0)))
    active_mdd = float(active.get("bear_window_mdd", active.get("bear_window_mdd_pct", -999.0)))
    if router_return > active_return and router_mdd >= active_mdd:
        return "BEAR_ROUTER_V685_SHADOW_CANDIDATE"
    return "BEAR_ROUTER_NEEDS_FORWARD_PAPER"
