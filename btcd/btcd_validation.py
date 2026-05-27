from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def validate_dominance_record(record: dict[str, Any], max_stale_minutes: int = 60) -> dict[str, Any]:
    dominance = _float(record.get("dominance"))
    source_updated_at = record.get("source_updated_at") or record.get("fetched_at")
    stale = _is_stale(source_updated_at, max_stale_minutes)
    valid_range = dominance is not None and 20.0 <= dominance <= 90.0
    return {
        "valid": bool(valid_range and not stale),
        "dominance_range_valid": bool(valid_range),
        "stale": stale,
        "data_quality": "GOOD" if valid_range and not stale else "STALE" if stale else "UNAVAILABLE",
        "reason": [] if valid_range and not stale else _reasons(valid_range, stale),
    }


def _reasons(valid_range: bool, stale: bool) -> list[str]:
    reasons: list[str] = []
    if not valid_range:
        reasons.append("DOMINANCE_OUT_OF_RANGE")
    if stale:
        reasons.append("SOURCE_STALE")
    return reasons


def _is_stale(value: Any, max_stale_minutes: int) -> bool:
    if not value:
        return False
    try:
        ts = pd.Timestamp(value)
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        now = pd.Timestamp(datetime.now(timezone.utc))
        return bool((now - ts).total_seconds() > max_stale_minutes * 60)
    except Exception:
        return False


def _float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
