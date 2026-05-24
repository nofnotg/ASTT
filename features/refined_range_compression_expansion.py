from __future__ import annotations

from features.source_quality_filters import source_quality_pass
from features.redesigned_candidate_sources import _candidate


def detect_range_compression_expansion_refined(snapshot: dict, config: dict | None = None) -> dict | None:
    quality = source_quality_pass(snapshot, (config or {}).get("order_krw", 500000))
    range_score = _range_compression_score(snapshot)
    if (
        range_score >= 55
        and float(snapshot.get("volume_burst_ratio_10s_vs_60s", 0.0)) >= 1.1
        and float(snapshot.get("buy_trade_ratio_10s", 0.0)) >= 0.45
        and float(snapshot.get("orderbook_imbalance", 0.0)) >= -0.05
        and quality["quality_pass"]
    ):
        return _candidate(snapshot, "RANGE_COMPRESSION_EXPANSION_REFINED", {"quality": quality, "range_compression_score": range_score}, "B")
    return None


def _range_compression_score(snapshot: dict) -> float:
    high_near = max(0.0, 1.0 - min(1.0, float(snapshot.get("previous_high_distance_pct", 999.0)) / 0.25))
    spread = max(0.0, 1.0 - min(1.0, float(snapshot.get("spread_pct", 999.0)) / 0.25))
    return (high_near * 60) + (spread * 40)
