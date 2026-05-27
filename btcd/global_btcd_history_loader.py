from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_HISTORY_PATH = Path("data/external/btc_dominance_history.csv")


def load_global_btcd_history(path: str | Path = DEFAULT_HISTORY_PATH) -> tuple[pd.DataFrame, dict[str, Any]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(), _quality(False, "GLOBAL_BTCD_DATA_REQUIRED", f"{csv_path} was not found. Fake history was not generated.")
    frame = pd.read_csv(csv_path)
    required = {"timestamp", "btc_dominance_pct", "source"}
    missing = sorted(required - set(frame.columns))
    if missing:
        return pd.DataFrame(), _quality(False, "GLOBAL_BTCD_DATA_REQUIRED", f"Missing required columns: {missing}")
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["btc_dominance_pct"] = pd.to_numeric(frame["btc_dominance_pct"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "btc_dominance_pct"]).sort_values("timestamp").reset_index(drop=True)
    frame = frame[(frame["btc_dominance_pct"] >= 20.0) & (frame["btc_dominance_pct"] <= 90.0)]
    if frame.empty:
        return frame, _quality(False, "GLOBAL_BTCD_DATA_REQUIRED", "CSV exists but contains no valid 20~90 dominance rows.")
    earliest = frame["timestamp"].min()
    latest = frame["timestamp"].max()
    actual_months = max((latest - earliest).days / 30.4375, 0.0)
    quality = "GOOD" if earliest <= pd.Timestamp("2022-12-31") and actual_months >= 12 else "PARTIAL"
    return frame, {
        "available": True,
        "source": "csv",
        "period": f"{earliest} ~ {latest}",
        "coverage": f"{len(frame)} rows; actual_months={actual_months:.2f}",
        "data_quality": quality,
        "notes": "Global BTC Dominance historical data loaded from user-provided CSV.",
        "earliest": str(earliest),
        "latest": str(latest),
        "actual_months_available": actual_months,
    }


def _quality(available: bool, data_quality: str, notes: str) -> dict[str, Any]:
    return {
        "available": available,
        "source": "unavailable",
        "period": "unavailable",
        "coverage": "0%",
        "data_quality": data_quality,
        "notes": notes,
        "actual_months_available": 0.0,
    }
