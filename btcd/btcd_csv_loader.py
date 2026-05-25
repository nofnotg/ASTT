from __future__ import annotations

from pathlib import Path

import pandas as pd


TIME_ALIASES = ("timestamp", "time", "date", "datetime")
DOMINANCE_ALIASES = ("btc_dominance_pct", "btc_dominance", "dominance", "btc_d")


def load_btcd_csv(path: str | Path = "data/external/btc_dominance.csv") -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(columns=["timestamp", "btc_dominance_pct", "source"])
    frame = pd.read_csv(csv_path)
    time_col = _find_column(frame, TIME_ALIASES)
    dominance_col = _find_column(frame, DOMINANCE_ALIASES)
    if not time_col or not dominance_col:
        raise ValueError("BTC dominance CSV requires timestamp and btc_dominance_pct columns")
    source_col = _find_column(frame, ("source",))
    output = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[time_col], errors="coerce"),
            "btc_dominance_pct": pd.to_numeric(frame[dominance_col], errors="coerce"),
            "source": frame[source_col].astype(str) if source_col else "csv",
        }
    )
    output = output.dropna(subset=["timestamp", "btc_dominance_pct"]).sort_values("timestamp")
    return output.reset_index(drop=True)


def _find_column(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    lowered = {str(col).lower(): col for col in frame.columns}
    for alias in aliases:
        if alias.lower() in lowered:
            return str(lowered[alias.lower()])
    return None

