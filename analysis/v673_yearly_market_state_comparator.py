from __future__ import annotations

from typing import Any


def extract_v673_yearly(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v673_yearly_market_state_v1",
        "yearly_comparison": summary.get("yearly_comparison", []),
        "market_state_pnl": summary.get("market_state_pnl", summary.get("regime_effect", [])),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
