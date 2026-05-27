from __future__ import annotations

from typing import Any


def extract_v67_yearly(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v67_global_btcd_yearly_v1",
        "yearly_comparison": summary.get("yearly_comparison", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
