from __future__ import annotations


def suggest_candidate(route: str, reason: str) -> dict[str, str | bool]:
    return {"route": route, "reason": reason, "status": "MANUAL_APPROVAL_REQUIRED", "active_change_applied": False}
