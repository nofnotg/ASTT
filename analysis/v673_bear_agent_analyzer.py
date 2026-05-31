from __future__ import annotations

from typing import Any


BEAR_AGENTS = {
    "RELATIVE_STRENGTH_BEAR_AGENT",
    "BEAR_DEFENSE_AGENT",
    "CASH_DEFENSE_AGENT",
    "BEAR_BOUNCE_V2_RESEARCH_AGENT",
}


def extract_v673_bear_agents(summary: dict[str, Any]) -> dict[str, Any]:
    rows = []
    by_name = {row.get("scenario"): row for row in summary.get("scenarios", [])}
    for agent in BEAR_AGENTS:
        row = dict(by_name.get(agent, {}))
        if not row:
            row = {
                "scenario": agent,
                "final_equity_krw": None,
                "total_return_pct": None,
                "mdd_pct": None,
                "profit_factor": None,
                "trade_count": 0,
                "decision": "RESEARCH_ONLY" if "BOUNCE" in agent else "DOMINANCE_DATA_REQUIRED",
            }
        rows.append(row)
    return {
        "schema_version": "v673_bear_agent_v1",
        "agents": rows,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
