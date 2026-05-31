from __future__ import annotations

from typing import Any


def lower_timeframe_coverage(journal: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "lower_timeframe_available": False,
        "timeframe": "1m|5m|15m",
        "covered_trade_count": 0,
        "uncovered_trade_count": len(journal),
        "coverage_pct": 0.0,
        "replayed_trade_count": 0,
        "price_path_resolved_count": 0,
        "price_path_ambiguous_count": len(journal),
        "reason": "No verified 1m/5m/15m path dataset is available; fake lower-timeframe data is forbidden.",
    }
