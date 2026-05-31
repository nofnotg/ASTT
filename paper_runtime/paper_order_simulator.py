from __future__ import annotations

from typing import Any


def simulate_order(decision: dict[str, Any]) -> dict[str, Any]:
    return {**decision, "order_execution": "simulated", "real_order_enabled": False, "live_order_allowed": False}
