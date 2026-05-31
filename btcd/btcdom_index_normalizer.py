from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from btcd.uploaded_btcdom_csv_loader import TIMEFRAMES, load_uploaded_btcdom_csv


def normalize_btcdom_index_files(
    external_dir: str | Path = "data/external",
    processed_dir: str | Path = "data/processed",
) -> dict[str, Any]:
    external_root = Path(external_dir)
    processed_root = Path(processed_dir)
    processed_root.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    starts: list[pd.Timestamp] = []
    ends: list[pd.Timestamp] = []
    close_min: list[float] = []
    close_max: list[float] = []
    source_types: set[str] = set()
    for timeframe in TIMEFRAMES:
        candidates = (
            external_root / f"btcdom_{timeframe}_2022_percent.csv",
            external_root / f"btcdom_{timeframe}_percent.csv",
            external_root / f"btcdom_{timeframe}_2022.csv",
            external_root / f"btcdom_{timeframe}.csv",
        )
        source_path = next((path for path in candidates if path.exists()), candidates[-1])
        frame, summary = load_uploaded_btcdom_csv(source_path)
        summary["timeframe"] = timeframe
        summary["selected_path"] = str(source_path)
        if not frame.empty:
            frame = frame.copy()
            frame["timeframe"] = timeframe
            frame["source"] = "uploaded_csv"
            frame["source_type"] = summary["source_type"]
            frame["is_percentage"] = bool(summary["is_percentage"])
            frame["lookahead_safe"] = True
            out = processed_root / f"btcdom_index_{timeframe}_normalized.csv"
            frame.to_csv(out, index=False)
            summary["normalized_path"] = str(out)
            starts.append(pd.Timestamp(summary["start"]))
            ends.append(pd.Timestamp(summary["end"]))
            close_min.append(float(summary["close_min"]))
            close_max.append(float(summary["close_max"]))
            source_types.add(str(summary["source_type"]))
        files[timeframe] = summary
    common_start = max(starts).isoformat() if starts else None
    common_end = min(ends).isoformat() if ends else None
    quality = "GOOD" if len(starts) == len(TIMEFRAMES) and common_start and common_end and common_start <= common_end else "PARTIAL"
    return {
        "schema_version": "v672_btcdom_index_data_quality_v1",
        "files": files,
        "source_type": source_types.pop() if len(source_types) == 1 else "MIXED_OR_UNKNOWN",
        "is_percentage": all(bool(item.get("is_percentage")) for item in files.values() if item.get("exists")),
        "close_min": min(close_min) if close_min else None,
        "close_max": max(close_max) if close_max else None,
        "common_coverage_start": common_start,
        "common_coverage_end": common_end,
        "data_quality": quality,
        "fake_data_generated": False,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
