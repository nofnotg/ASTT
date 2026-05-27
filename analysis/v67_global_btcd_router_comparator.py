from __future__ import annotations

from typing import Any


def compact_router_summary(summary: dict[str, Any]) -> dict[str, Any]:
    scenario = next((row for row in summary.get("scenarios", []) if row.get("scenario") == "GLOBAL_BTCD_COMPACT_ROUTER"), {})
    return {
        "schema_version": "v67_global_btcd_compact_router_v1",
        "scenario": scenario,
        "saved_loss_missed_profit": next((row for row in summary.get("saved_loss_missed_profit", []) if row.get("scenario") == "GLOBAL_BTCD_COMPACT_ROUTER"), {}),
        "audit": summary.get("audit", {}),
        "decision": scenario.get("decision", "GLOBAL_BTCD_DATA_REQUIRED"),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
