from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def get_or_build_feature_snapshot(
    market: str,
    as_of_time,
    timeframes: dict,
    config: dict,
    cache_dir: str = "replay_store/feature_cache/v53",
) -> dict:
    """Cache compact as-of feature snapshots without storing future rows."""

    as_of = pd.Timestamp(as_of_time)
    rounded = as_of.floor(_infer_boundary(config))
    cache_root = Path(cache_dir)
    cache_root.mkdir(parents=True, exist_ok=True)
    key = _snapshot_key(market, rounded, config)
    path = cache_root / f"{key}.json"
    if path.exists():
        return {"cache_hit": True, "snapshot": json.loads(path.read_text(encoding="utf-8")), "cache_key": key, "path": str(path)}

    snapshot = {
        "market": market,
        "as_of_time": rounded.isoformat(),
        "config_hash": _config_hash(config),
        "timeframes": {},
    }
    for name, frame in timeframes.items():
        filtered = _filter_as_of(frame, as_of)
        snapshot["timeframes"][name] = _summarize_frame(filtered, as_of)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"cache_hit": False, "snapshot": snapshot, "cache_key": key, "path": str(path)}


def _filter_as_of(frame: Any, as_of: pd.Timestamp) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    data = frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)
    if data.empty or "time" not in data.columns:
        return data.iloc[0:0] if isinstance(data, pd.DataFrame) else pd.DataFrame()
    times = pd.to_datetime(data["time"], errors="coerce")
    return data[times <= as_of].copy()


def _summarize_frame(frame: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    if frame.empty:
        return {"row_count": 0, "latest_time": None, "latest_close": None, "future_rows_included": False}
    latest_time = pd.Timestamp(frame.iloc[-1]["time"])
    latest_close = float(frame.iloc[-1].get("close", 0.0))
    return {
        "row_count": int(len(frame)),
        "latest_time": latest_time.isoformat(),
        "latest_close": latest_close,
        "future_rows_included": bool(latest_time > as_of),
    }


def _snapshot_key(market: str, as_of: pd.Timestamp, config: dict) -> str:
    raw = f"{market}|{as_of.isoformat()}|{_config_hash(config)}|v53"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _config_hash(config: dict) -> str:
    payload = json.dumps(config or {}, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _infer_boundary(config: dict) -> str:
    timeframe = str((config or {}).get("timeframe", "1min"))
    return {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "60min"}.get(timeframe, "1min")
