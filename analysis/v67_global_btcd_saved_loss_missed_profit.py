from __future__ import annotations

from typing import Any


def extract_v67_saved_loss(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v67_global_btcd_saved_loss_v1",
        "saved_loss_missed_profit": summary.get("saved_loss_missed_profit", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
