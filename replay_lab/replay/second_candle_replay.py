from __future__ import annotations

from pathlib import Path

import pandas as pd

from live_data.second_candle_collector import fill_missing_seconds
from replay_lab.paths import REPLAY_STORE_DIR


def replay_second_candles(market: str, start_time, end_time, fill_missing_seconds: bool = True, store_dir: Path = REPLAY_STORE_DIR) -> dict:
    start = pd.Timestamp(start_time)
    end = pd.Timestamp(end_time)
    frames = []
    root = store_dir / "normalized" / "upbit_seconds" / market
    day = start.normalize()
    while day <= end.normalize():
        path = root / f"{day.date().isoformat()}.parquet"
        if path.exists():
            frame = pd.read_parquet(path)
            frame["time"] = pd.to_datetime(frame.get("candle_time_kst", frame.get("time")))
            frames.append(frame)
        day += pd.Timedelta(days=1)
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not data.empty:
        data = data[(data["time"] >= start) & (data["time"] <= end)].copy()
    actual = int(len(data))
    if fill_missing_seconds:
        filled = fill_missing_seconds_fn(data, start, end)
    else:
        filled = data
        filled["synthetic"] = False if not filled.empty else []
    synthetic = int(filled["synthetic"].sum()) if not filled.empty and "synthetic" in filled else 0
    expected = int((end - start).total_seconds()) + 1
    missing = max(0, expected - actual)
    if actual == 0:
        quality = "UNAVAILABLE"
    elif synthetic / max(expected, 1) > 0.5:
        quality = "POOR"
    elif synthetic:
        quality = "PARTIAL"
    else:
        quality = "GOOD"
    return {"market": market, "start_time": start.isoformat(), "end_time": end.isoformat(), "seconds": filled.to_dict("records"), "actual_second_count": actual, "missing_second_count": missing, "synthetic_second_count": synthetic, "data_quality": quality}


def fill_missing_seconds_fn(frame: pd.DataFrame, start, end) -> pd.DataFrame:
    return fill_missing_seconds(frame, start, end)
