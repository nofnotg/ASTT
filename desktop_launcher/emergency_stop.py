from __future__ import annotations

from typing import Any


def emergency_stop_plan() -> dict[str, Any]:
    return {"stops": ["paper_runtime", "dashboard"], "live_order_cancel": False, "withdraw": False}
