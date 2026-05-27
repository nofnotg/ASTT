from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pandas as pd


TIMEFRAMES = ("1h", "4h", "1d")


def copy_uploaded_btcdom_csvs(
    source_dir: str | Path = "C:/ASTT",
    external_dir: str | Path = "data/external",
) -> dict[str, Any]:
    source_root = Path(source_dir)
    if (source_root / "btc_dom").exists():
        source_root = source_root / "btc_dom"
    target_root = Path(external_dir)
    target_root.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES:
        filename = f"btcdom_{timeframe}_percent.csv" if (source_root / f"btcdom_{timeframe}_percent.csv").exists() else f"btcdom_{timeframe}.csv"
        source = source_root / filename
        target = target_root / filename
        exists = source.exists()
        copied = False
        if exists:
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            copied = target.exists()
        files[timeframe] = {
            "source_path": str(source),
            "target_path": str(target),
            "exists": exists,
            "copied": copied,
            "size_bytes": source.stat().st_size if exists else 0,
        }
    return files


def load_uploaded_btcdom_csv(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(), {"exists": False, "quality": "MISSING", "reason": "FILE_NOT_FOUND"}
    frame = _read_csv(csv_path)
    original_rows = len(frame)
    frame.columns = [str(col).strip().lower() for col in frame.columns]
    timestamp_col = _timestamp_column(frame)
    if not timestamp_col:
        return pd.DataFrame(), {"exists": True, "rows": original_rows, "quality": "BAD", "reason": "TIMESTAMP_COLUMN_MISSING"}
    if "datetime_utc" in frame.columns:
        timestamp = pd.to_datetime(frame["datetime_utc"], errors="coerce", utc=True)
    elif "datetime" in frame.columns:
        timestamp = pd.to_datetime(frame["datetime"], errors="coerce", utc=True)
    else:
        timestamp = _parse_timestamp(frame[timestamp_col])
    frame["timestamp"] = timestamp
    for col in ("open", "high", "low", "close"):
        pct_col = f"{col}_pct"
        raw_col = f"{col}_raw"
        if pct_col in frame.columns:
            frame[col] = pd.to_numeric(frame[pct_col], errors="coerce")
        elif col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        elif raw_col in frame.columns:
            frame[col] = pd.to_numeric(frame[raw_col], errors="coerce")
        else:
            frame[col] = 0.0
    frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce") if "volume" in frame.columns else 0.0
    frame = frame.dropna(subset=["timestamp", "close"]).sort_values("timestamp")
    duplicate_count = int(frame["timestamp"].duplicated().sum())
    frame = frame.drop_duplicates(subset=["timestamp"], keep="last")
    missing_count = int(frame[["open", "high", "low", "close"]].isna().sum().sum())
    normalized = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    source_type, is_percentage = classify_btcdom_source_type(normalized["close"], frame)
    quality = "GOOD" if not normalized.empty and missing_count == 0 else "PARTIAL"
    summary = {
        "exists": True,
        "rows": len(normalized),
        "original_rows": original_rows,
        "duplicate_count": duplicate_count,
        "missing_count": missing_count,
        "start": normalized["timestamp"].min().isoformat() if not normalized.empty else None,
        "end": normalized["timestamp"].max().isoformat() if not normalized.empty else None,
        "close_min": float(normalized["close"].min()) if not normalized.empty else None,
        "close_max": float(normalized["close"].max()) if not normalized.empty else None,
        "source_type": source_type,
        "is_percentage": is_percentage,
        "quality": quality,
    }
    return normalized, summary


def classify_btcdom_source_type(close: pd.Series, frame: pd.DataFrame | None = None) -> tuple[str, bool]:
    valid = pd.to_numeric(pd.Series(close), errors="coerce").dropna()
    if valid.empty:
        return "UNKNOWN", False
    if frame is not None and "source_note" in frame.columns:
        note = " ".join(str(value) for value in frame["source_note"].dropna().head(5))
        if "not CMC" in note or "not CMC/TradingView" in note or "raw value divided by 100" in note:
            return "BTCDOM_INDEX_PROXY", False
    in_percentage_range = ((valid >= 0) & (valid <= 100)).mean()
    if in_percentage_range >= 0.95:
        return "GLOBAL_BTCD_PERCENTAGE", True
    return "BTCDOM_INDEX_PROXY", False


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _timestamp_column(frame: pd.DataFrame) -> str | None:
    for col in ("timestamp", "timestamp_ms", "datetime", "datetime_utc", "close_time", "time", "date"):
        if col in frame.columns:
            return col
    return None


def _parse_timestamp(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.8:
        unit = "ms" if numeric.dropna().median() > 10_000_000_000 else "s"
        return pd.to_datetime(numeric, unit=unit, errors="coerce", utc=True)
    return pd.to_datetime(series, errors="coerce", utc=True)
