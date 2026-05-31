from __future__ import annotations

from typing import Any


def score_ltf_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"row_count": 0, "quality": "MISSING", "has_ohlc": False, "duplicate_timestamp_count": 0}
    seen: set[str] = set()
    duplicate = 0
    has_ohlc = True
    for row in rows:
        ts = str(row.get("timestamp", ""))
        if ts in seen:
            duplicate += 1
        seen.add(ts)
        has_ohlc = has_ohlc and all(float(row.get(key, 0.0) or 0.0) > 0.0 for key in ("open", "high", "low", "close"))
    quality = "GOOD" if has_ohlc and duplicate == 0 else "WARN"
    return {"row_count": len(rows), "quality": quality, "has_ohlc": has_ohlc, "duplicate_timestamp_count": duplicate}
