from __future__ import annotations

import pandas as pd


def detect_fvg(frame: pd.DataFrame, timeframe: str = "1h") -> list[dict]:
    zones = []
    if frame is None or len(frame) < 3:
        return zones
    data = frame.reset_index(drop=True)
    for idx in range(1, len(data) - 1):
        prev = data.iloc[idx - 1]
        nxt = data.iloc[idx + 1]
        if float(prev["high"]) < float(nxt["low"]):
            low, high = float(prev["high"]), float(nxt["low"])
            zones.append(_zone("BULLISH_FVG", timeframe, low, high, data.iloc[idx]["time"]))
        if float(prev["low"]) > float(nxt["high"]):
            low, high = float(nxt["high"]), float(prev["low"])
            zones.append(_zone("BEARISH_FVG", timeframe, low, high, data.iloc[idx]["time"]))
    return zones[-10:]


def _zone(zone_type: str, timeframe: str, low: float, high: float, created_at) -> dict:
    mid = (low + high) / 2
    gap = (high - low) / max(mid, 1e-9) * 100
    return {
        "zone_type": zone_type,
        "timeframe": timeframe,
        "zone_low": low,
        "zone_high": high,
        "gap_size_pct": gap,
        "created_at": str(created_at),
        "quality_score": min(100.0, 40.0 + gap * 20.0),
    }
