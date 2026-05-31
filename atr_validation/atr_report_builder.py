from __future__ import annotations

from typing import Any


def atr_decision(rows: list[dict[str, Any]], lower_timeframe_available: bool) -> str:
    conservative = next((row for row in rows if row.get("model") == "conservative"), {})
    if not lower_timeframe_available:
        return "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
    if conservative and str(conservative.get("decision", "")).endswith("CANDIDATE"):
        return "ATR_VALIDATED_SHADOW_CANDIDATE"
    return "ATR_DATA_INSUFFICIENT"
