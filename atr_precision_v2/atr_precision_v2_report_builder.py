from __future__ import annotations

from typing import Any


def final_atr_decision(coverage: dict[str, Any], conservative_row: dict[str, Any], active_row: dict[str, Any] | None = None) -> str:
    if float(coverage.get("best_coverage_pct", 0.0)) < 80.0:
        return "ATR_DATA_INSUFFICIENT"
    if float(conservative_row.get("lookahead_fail_count", 0.0)) > 0.0:
        return "ATR_REJECTED"
    if active_row and float(conservative_row.get("return_pct", -999.0)) > float(active_row.get("return_pct", -999.0)) and float(conservative_row.get("mdd_pct", -999.0)) >= float(active_row.get("mdd_pct", -999.0)):
        return "ATR_VALIDATED_SHADOW_CANDIDATE"
    return "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
