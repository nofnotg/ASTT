from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_upbit_btc_flow_dominance(
    archive_dir: str | Path = "replay_store/historical_archive",
    fallback_dir: str | Path = "replay_store/v6_ohlcv",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = _choose_root(Path(archive_dir), Path(fallback_dir))
    daily_dir = root / "1d"
    if not daily_dir.exists():
        return pd.DataFrame(), _quality(False, "unavailable", "No 1d OHLCV directory found.")

    frames: list[pd.DataFrame] = []
    market_names: set[str] = set()
    for path in sorted(daily_dir.glob("KRW-*.parquet")):
        frame = pd.read_parquet(path)
        if frame.empty or "time" not in frame:
            continue
        quote_col = "trade_price" if "trade_price" in frame else "quote_volume" if "quote_volume" in frame else None
        if quote_col is None:
            continue
        market_names.add(str(frame["market"].iloc[0]) if "market" in frame and not frame.empty else path.stem)
        slim = frame[["market", "time", quote_col]].copy()
        slim["time"] = pd.to_datetime(slim["time"], errors="coerce").dt.floor("D")
        slim["quote_volume"] = pd.to_numeric(slim[quote_col], errors="coerce").fillna(0.0)
        frames.append(slim[["market", "time", "quote_volume"]])
    if not frames:
        return pd.DataFrame(), _quality(False, str(root), "No readable KRW daily OHLCV parquet files.")

    all_rows = pd.concat(frames, ignore_index=True).dropna(subset=["time"])
    total = all_rows.groupby("time", as_index=False)["quote_volume"].sum().rename(columns={"quote_volume": "total_quote_volume"})
    btc = all_rows[all_rows["market"].astype(str) == "KRW-BTC"].groupby("time", as_index=False)["quote_volume"].sum().rename(columns={"quote_volume": "btc_quote_volume"})
    if btc.empty:
        return pd.DataFrame(), _quality(False, str(root), "KRW-BTC daily OHLCV was not available; proxy cannot be calculated.")
    merged = total.merge(btc, on="time", how="left").fillna({"btc_quote_volume": 0.0})
    merged["upbit_btc_flow_dominance_pct"] = merged.apply(
        lambda row: row["btc_quote_volume"] / row["total_quote_volume"] * 100.0 if row["total_quote_volume"] > 0 else 0.0,
        axis=1,
    )
    alt_rows = all_rows[all_rows["market"].astype(str) != "KRW-BTC"].copy()
    alt_rows["alt_volume_positive"] = alt_rows["quote_volume"] > 0
    breadth = alt_rows.groupby("time", as_index=False)["alt_volume_positive"].mean().rename(columns={"alt_volume_positive": "alt_volume_breadth"})
    merged = merged.merge(breadth, on="time", how="left").fillna({"alt_volume_breadth": 0.0}).sort_values("time")
    merged["flow_delta_1d"] = merged["upbit_btc_flow_dominance_pct"].diff(1)
    merged["flow_delta_7d"] = merged["upbit_btc_flow_dominance_pct"].diff(7)
    rolling_mean = merged["upbit_btc_flow_dominance_pct"].rolling(30, min_periods=5).mean()
    rolling_std = merged["upbit_btc_flow_dominance_pct"].rolling(30, min_periods=5).std().replace(0, pd.NA)
    zscore = (merged["upbit_btc_flow_dominance_pct"] - rolling_mean) / rolling_std
    merged["flow_zscore_30d"] = pd.to_numeric(zscore, errors="coerce").fillna(0.0)
    merged["flow_regime"] = merged.apply(_flow_regime, axis=1)
    note = (
        f"{len(merged)} daily rows from {merged['time'].min()} to {merged['time'].max()}; "
        f"{len(market_names)} KRW markets. This is an Upbit proxy, not global BTC dominance."
    )
    return merged.reset_index(drop=True), _quality(
        True,
        str(root),
        note,
    )


def _choose_root(primary: Path, fallback: Path) -> Path:
    if (primary / "1d" / "KRW-BTC.parquet").exists():
        return primary
    return fallback if (fallback / "1d" / "KRW-BTC.parquet").exists() else primary


def _flow_regime(row: pd.Series) -> str:
    delta_7d = float(row.get("flow_delta_7d") or 0.0)
    zscore = float(row.get("flow_zscore_30d") or 0.0)
    if zscore >= 1.5 and delta_7d > 0:
        return "BTC_FLOW_SPIKE"
    if delta_7d >= 1.0:
        return "BTC_FLOW_RISING"
    if delta_7d <= -1.0:
        return "BTC_FLOW_FALLING"
    return "BTC_FLOW_STABLE"


def _quality(available: bool, source: str, notes: str) -> dict[str, Any]:
    return {
        "available": available,
        "source": source,
        "period": "calculated from Upbit KRW OHLCV proxy" if available else "unavailable",
        "coverage": notes,
        "notes": notes,
    }
