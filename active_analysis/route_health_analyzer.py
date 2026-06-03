from __future__ import annotations

from scenario_telemetry.v688_common import ACTIVE_ROUTE


def route_state(backfill: dict, runtime: dict, genome: dict | None = None) -> dict:
    display = (genome or {}).get("route_state", {}).get("display_primary_route") or backfill.get("active_route") or ACTIVE_ROUTE
    actual = backfill.get("active_route") or runtime.get("active_route") or ACTIVE_ROUTE
    forward = runtime.get("active_route") or ACTIVE_ROUTE
    return {
        "display_primary_route": display,
        "actual_paper_primary_route": actual,
        "forward_runner_route": forward,
        "mismatch_warning": display != actual or forward != actual,
    }
