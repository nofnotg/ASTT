from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


TIME_ALIASES = ("time", "timestamp", "date", "datetime")
DOMINANCE_ALIASES = ("btc_dominance", "dominance", "btc_d")


def load_btc_dominance_data(path: str) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(path)
    if source.suffix.lower() == ".parquet":
        frame = pd.read_parquet(source)
    else:
        frame = pd.read_csv(source)
    return _normalize(frame)


def align_dominance_to_replay_time(
    dominance_frame: pd.DataFrame,
    as_of_time,
    tolerance_minutes: int = 60,
) -> dict:
    if dominance_frame is None or dominance_frame.empty:
        return _missing("dominance_unavailable")
    frame = _normalize(dominance_frame)
    as_of = pd.Timestamp(as_of_time)
    history = frame[frame["time"] <= as_of].copy()
    if history.empty:
        return _missing("no_dominance_before_as_of")
    current = history.iloc[-1]
    stale_minutes = (as_of - pd.Timestamp(current["time"])).total_seconds() / 60
    warnings: list[str] = []
    stale = stale_minutes > tolerance_minutes
    if stale:
        warnings.append("stale_dominance")

    return {
        "dominance_available": True,
        "dominance_value": float(current["btc_dominance"]),
        "dominance_change_1h": _change(history, current, "1h"),
        "dominance_change_4h": _change(history, current, "4h"),
        "dominance_change_1d": _change(history, current, "1D"),
        "stale": stale,
        "warnings": warnings,
    }


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    time_col = _first_column(data, TIME_ALIASES)
    dom_col = _first_column(data, DOMINANCE_ALIASES)
    if not time_col or not dom_col:
        raise ValueError("dominance data requires time and btc_dominance columns")
    data = data.rename(columns={time_col: "time", dom_col: "btc_dominance"})
    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    data["btc_dominance"] = pd.to_numeric(data["btc_dominance"], errors="coerce")
    data = data.dropna(subset=["time", "btc_dominance"]).sort_values("time")
    return data[["time", "btc_dominance"]].reset_index(drop=True)


def _first_column(frame: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    lower = {str(col).lower(): col for col in frame.columns}
    for name in names:
        if name in lower:
            return lower[name]
    return None


def _change(history: pd.DataFrame, current: pd.Series, window: str) -> float | None:
    cutoff = pd.Timestamp(current["time"]) - pd.Timedelta(window)
    prior = history[history["time"] <= cutoff]
    if prior.empty:
        return None
    return float(current["btc_dominance"] - prior.iloc[-1]["btc_dominance"])


def _missing(reason: str) -> dict[str, Any]:
    return {
        "dominance_available": False,
        "dominance_value": None,
        "dominance_change_1h": None,
        "dominance_change_4h": None,
        "dominance_change_1d": None,
        "stale": True,
        "warnings": [reason],
    }
