from __future__ import annotations

import pandas as pd


def detect_order_blocks(frame: pd.DataFrame, timeframe: str = "1h") -> list[dict]:
    if frame is None or len(frame) < 10:
        return []
    data = frame.reset_index(drop=True)
    blocks = []
    avg_volume = float(data["volume"].tail(30).mean())
    for idx in range(1, len(data)):
        prev = data.iloc[idx - 1]
        now = data.iloc[idx]
        body_pct = abs(float(now["close"]) - float(now["open"])) / max(float(now["open"]), 1e-9) * 100
        if body_pct < 0.6:
            continue
        if float(now["close"]) > float(now["open"]) and float(prev["close"]) < float(prev["open"]):
            blocks.append(_block("BULLISH_ORDER_BLOCK", timeframe, prev, avg_volume))
        if float(now["close"]) < float(now["open"]) and float(prev["close"]) > float(prev["open"]):
            blocks.append(_block("BEARISH_ORDER_BLOCK", timeframe, prev, avg_volume))
    return blocks[-10:]


def _block(zone_type: str, timeframe: str, row, avg_volume: float) -> dict:
    volume_score = min(100.0, float(row["volume"]) / max(avg_volume, 1e-9) * 50.0)
    return {
        "zone_type": zone_type,
        "timeframe": timeframe,
        "zone_low": float(row["low"]),
        "zone_high": float(row["high"]),
        "volume_score": volume_score,
        "quality_score": min(100.0, 45.0 + volume_score * 0.4),
    }
