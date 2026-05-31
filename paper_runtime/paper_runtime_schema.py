from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REAL_ORDER_ENABLED = False
LIVE_ORDER_ALLOWED = False
AUTO_APPLY_ALLOWED = False


def safety_flags() -> dict[str, bool]:
    return {
        "real_order_enabled": REAL_ORDER_ENABLED,
        "live_order_allowed": LIVE_ORDER_ALLOWED,
        "auto_apply_allowed": AUTO_APPLY_ALLOWED,
    }


@dataclass(frozen=True)
class RouteSpec:
    route_id: str
    status: str
    version: str = "v683"
    enabled: bool = True
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "status": self.status,
            "version": self.version,
            "enabled": self.enabled,
            "notes": self.notes,
            **safety_flags(),
        }
