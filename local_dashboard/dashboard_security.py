from __future__ import annotations

from paper_runtime.paper_runtime_schema import safety_flags


FORBIDDEN_ENDPOINT_PARTS = ("order", "orders", "withdraw", "cancel", "live-trade", "live_order")


def security_status() -> dict[str, object]:
    return {
        "live_order_endpoints_enabled": False,
        "route_switch_endpoint_enabled": False,
        "llm_can_change_active": False,
        **safety_flags(),
    }


def is_forbidden_path(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in FORBIDDEN_ENDPOINT_PARTS)
