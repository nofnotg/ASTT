from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from paper_runtime.paper_runtime_schema import RouteSpec, safety_flags


ACTIVE_ROUTE = "LG_V2_BALANCED_PLUS_DOM_GATE"
DEFAULT_SHADOW_ROUTES = [
    "LG_M3_PF0.8_DD8",
    "LOSS_GUARD_2026_ROUTER_V1_SHADOW",
    "BASE_BALANCED",
    "BASE_ROLLING",
]


def route_registry(active_route: str = ACTIVE_ROUTE, shadow_routes: list[str] | None = None) -> dict[str, Any]:
    shadows = list(shadow_routes or DEFAULT_SHADOW_ROUTES)
    specs = [RouteSpec(active_route, "ACTIVE").as_dict()]
    specs.extend(RouteSpec(route, "SHADOW").as_dict() for route in shadows if route != active_route)
    return {
        "active_route": active_route,
        "shadow_routes": shadows,
        "routes": specs,
        "route_switch_locked": True,
        "active_auto_switch_allowed": False,
        **safety_flags(),
    }


def switch_active_route(route: str, confirm_switch: bool = False, registry_path: str | Path | None = None) -> dict[str, Any]:
    if not confirm_switch:
        return {
            "route": route,
            "switched": False,
            "reason": "confirm-switch required",
            "route_switch_locked": True,
            "decision": "MANUAL_APPROVAL_REQUIRED",
            **safety_flags(),
        }
    registry = route_registry(route, [item for item in DEFAULT_SHADOW_ROUTES if item != route])
    registry["route_event"] = {"event": "MANUAL_SWITCH_CONFIRMED", "route": route, "ts": datetime.utcnow().isoformat()}
    if registry_path:
        path = Path(registry_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(__import__("json").dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"route": route, "switched": True, "decision": "PAPER_ROUTE_ACTIVE", **registry}
