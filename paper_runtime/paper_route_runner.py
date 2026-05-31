from __future__ import annotations

from typing import Any


def paper_route_decision(route: str, context: dict[str, Any]) -> dict[str, Any]:
    return {"route": route, "context_id": context.get("trade_id"), "decision": "PAPER_ROUTE_SHADOW" if context.get("shadow") else "PAPER_ROUTE_ACTIVE"}
