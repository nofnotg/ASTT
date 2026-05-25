from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_ohlcv_coverage(data_dir: str | Path = "replay_store/v6_ohlcv", requested_months: int = 36) -> dict[str, Any]:
    root = Path(data_dir)
    by_timeframe: dict[str, Any] = {}
    earliest = None
    latest = None
    markets: set[str] = set()
    for tf_dir in sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []:
        candle_count = 0
        tf_markets = []
        for path in sorted(tf_dir.glob("*.parquet")):
            frame = pd.read_parquet(path)
            if frame.empty:
                continue
            tf_markets.append(path.stem)
            markets.add(path.stem)
            candle_count += len(frame)
            times = pd.to_datetime(frame["time"])
            first = times.min()
            last = times.max()
            earliest = first if earliest is None or first < earliest else earliest
            latest = last if latest is None or last > latest else latest
        by_timeframe[tf_dir.name] = {"markets": len(tf_markets), "candles": candle_count, "status": "OK" if candle_count else "MISSING"}
    actual_months = 0.0
    if earliest is not None and latest is not None:
        actual_months = max(0.0, (latest - earliest).days / 30.4375)
    insufficient = sorted(markets) if actual_months < requested_months * 0.8 else []
    return {
        "schema_version": "v6.1",
        "requested_months": requested_months,
        "actual_months_available": actual_months,
        "market_count": len(markets),
        "candle_count_by_timeframe": by_timeframe,
        "earliest_candle_time": str(earliest) if earliest is not None else None,
        "latest_candle_time": str(latest) if latest is not None else None,
        "missing_market_count": 0,
        "insufficient_history_market_count": len(insufficient),
        "insufficient_history_markets": insufficient[:20],
        "newly_listed_market_count": len(insufficient),
        "newly_listed_markets": insufficient[:20],
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
