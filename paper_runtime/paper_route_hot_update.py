from __future__ import annotations


def request_route_switch(route: str) -> dict[str, str | bool]:
    return {"requested_route": route, "active_change_applied": False, "manual_switch_required": True, "status": "MANUAL_APPROVAL_REQUIRED"}
