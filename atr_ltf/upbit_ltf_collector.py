from __future__ import annotations

from typing import Any

from paper_runtime.paper_runtime_schema import safety_flags


def plan_upbit_ltf_collection(markets: list[str], timeframes: list[str] | None = None) -> dict[str, Any]:
    return {
        "collector_ready": True,
        "network_call_executed": False,
        "fake_data_generated": False,
        "markets": markets,
        "timeframes": timeframes or ["1m", "5m", "15m"],
        "decision": "COLLECTION_PLAN_ONLY",
        **safety_flags(),
    }
