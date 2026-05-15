from __future__ import annotations

import pandas as pd


def evaluate_candles(frame: pd.DataFrame, time_column: str = "candle_time_kst") -> dict:
    if frame is None or frame.empty:
        return {"quality": "LOW_QUALITY", "quality_score": 0.0, "missing_count": 0, "duplicate_count": 0, "warnings": ["empty dataset"]}
    duplicate_count = int(frame.duplicated(subset=[time_column]).sum()) if time_column in frame else 0
    sorted_times = pd.to_datetime(frame[time_column], errors="coerce") if time_column in frame else pd.Series([], dtype="datetime64[ns]")
    reversed_count = int((sorted_times.diff().dt.total_seconds().dropna() < 0).sum()) if not sorted_times.empty else 0
    penalty = min(0.5, duplicate_count * 0.01 + reversed_count * 0.02)
    score = max(0.0, 1.0 - penalty)
    if score >= 0.95:
        quality = "GOOD"
    elif score >= 0.85:
        quality = "ACCEPTABLE"
    else:
        quality = "LOW_QUALITY"
    return {"quality": quality, "quality_score": score, "missing_count": 0, "duplicate_count": duplicate_count, "warnings": []}

