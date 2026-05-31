from __future__ import annotations

from typing import Any


def review_paper_state(state: dict[str, Any]) -> dict[str, Any]:
    return {"active_change_applied": False, "manual_switch_required": True, "risk_flags": ["LIVE_NOT_ALLOWED"], "state": state}
