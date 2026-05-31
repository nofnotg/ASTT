from __future__ import annotations

from typing import Any


def extract_v673_router(summary: dict[str, Any]) -> dict[str, Any]:
    rows = summary.get("scenarios", [])
    control = next((row for row in rows if row.get("scenario") == "POLICY_BLEND_CONTROL"), {})
    router = next((row for row in rows if row.get("scenario") == "SCENARIO_AGENT_ROUTER_V1"), {})
    return {
        "schema_version": "v673_scenario_agent_router_v1",
        "scenarios": [control, router],
        "lookahead_audit": summary.get("lookahead_audit", {}),
        "market_state_pnl": summary.get("market_state_pnl", []),
        "router_journal": summary.get("router_journal", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
