from __future__ import annotations

from features.source_quality_filters import source_quality_pass
from features.redesigned_candidate_sources import _candidate


def detect_orderflow_surge_refined(snapshot: dict, config: dict | None = None) -> dict | None:
    quality = source_quality_pass(snapshot, (config or {}).get("order_krw", 500000))
    if (
        float(snapshot.get("buy_trade_ratio_5s", 0.0)) >= 0.52
        and float(snapshot.get("buy_trade_ratio_10s", 0.0)) >= 0.50
        and float(snapshot.get("orderbook_imbalance", 0.0)) > 0
        and quality["quality_pass"]
    ):
        return _candidate(snapshot, "ORDERFLOW_SURGE_REFINED", {"quality": quality}, "B")
    return None
