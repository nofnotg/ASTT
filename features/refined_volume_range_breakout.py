from __future__ import annotations

from features.source_quality_filters import source_quality_pass
from features.redesigned_candidate_sources import _candidate


def detect_volume_range_breakout_refined(snapshot: dict, config: dict | None = None) -> dict | None:
    quality = source_quality_pass(snapshot, (config or {}).get("order_krw", 500000))
    if (
        float(snapshot.get("volume_burst_ratio_10s_vs_60s", 0.0)) >= 1.2
        and float(snapshot.get("trade_count_acceleration", 0.0)) > 0
        and float(snapshot.get("previous_high_distance_pct", 999.0)) <= 0.20
        and float(snapshot.get("breakout_distance_pct", 0.0)) >= 0
        and quality["quality_pass"]
    ):
        return _candidate(snapshot, "VOLUME_RANGE_BREAKOUT_REFINED", {"quality": quality}, "B")
    return None
