from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from btcd.btcd_csv_loader import load_btcd_csv


def load_global_btcd(path: str | Path = "data/external/btc_dominance.csv") -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = load_btcd_csv(path)
    if frame.empty:
        return frame, {
            "available": False,
            "source": "unavailable",
            "period": "unavailable",
            "coverage": "0%",
            "notes": "data/external/btc_dominance.csv was not found. Fake dominance was not generated.",
        }
    earliest = str(frame["timestamp"].min())
    latest = str(frame["timestamp"].max())
    return frame, {
        "available": True,
        "source": "csv",
        "period": f"{earliest} ~ {latest}",
        "coverage": f"{len(frame)} rows",
        "notes": "Global BTC Dominance loaded from local CSV.",
    }

