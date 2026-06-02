from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from market_data.ohlcv_store import OHLCVStore, normalize_ohlcv
from market_data.timeframe_resampler import resample_ohlcv
from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.paths import REPLAY_STORE_DIR


DEFAULT_TIMEFRAMES = ["1d", "4h", "1h", "15m", "5m", "1m"]


def collect_upbit_historical_archive(
    markets: str = "TOP_KRW_50",
    timeframes: str = "1d,4h,1h,15m,5m,1m",
    max_lookback_days: int = 1460,
    archive_dir: str | Path = REPLAY_STORE_DIR / "historical_archive",
    loader: HistoricalLoader | None = None,
) -> dict[str, Any]:
    loader = loader or HistoricalLoader()
    selected_markets = _resolve_markets(markets, loader)
    requested = [item.strip() for item in timeframes.split(",") if item.strip()]
    end = datetime.now().replace(microsecond=0)
    start = end - timedelta(days=max_lookback_days)
    store = OHLCVStore(archive_dir)
    rows = []
    stop_reasons: dict[str, str] = {}

    for market in selected_markets:
        for timeframe in requested:
            try:
                path = loader.load_candles(market, _loader_timeframe(timeframe), start, end)
                frame = _read_loader_frame(path, timeframe, market)
                if frame.empty:
                    frame = store.load(timeframe, market)
                if not frame.empty:
                    store.save(timeframe, market, frame)
                    if timeframe == "1d":
                        weekly = resample_ohlcv(frame, "1w", market)
                        if not weekly.empty:
                            store.save("1w", market, weekly)
                rows.append(_coverage_row(market, timeframe, frame, "OK" if not frame.empty else "EMPTY"))
                _write_running_summary(markets, selected_markets, requested, max_lookback_days, rows, stop_reasons, archive_dir)
            except Exception as exc:  # public data collection must keep partial archive
                stop_reasons[f"{market}:{timeframe}"] = type(exc).__name__
                rows.append(
                    {
                        "market": market,
                        "timeframe": timeframe,
                        "candles": 0,
                        "earliest_available_time": None,
                        "latest_time": None,
                        "actual_months_available": 0.0,
                        "status": "PARTIAL_OR_FAILED",
                        "api_limit_stop_reason": type(exc).__name__,
                    }
                )
                _write_running_summary(markets, selected_markets, requested, max_lookback_days, rows, stop_reasons, archive_dir)

    weekly_rows = [_coverage_row(market, "1w", store.load("1w", market), "DERIVED_FROM_1D") for market in selected_markets]
    summary = _summary(markets, selected_markets, [*requested, "1w"], max_lookback_days, [*rows, *weekly_rows], stop_reasons)
    _write(Path("docs/reports/latest_historical_archive_summary.json"), summary)
    _write(Path(archive_dir) / "latest_historical_archive_summary.json", summary)
    return summary


def _resolve_markets(markets: str, loader: HistoricalLoader) -> list[str]:
    if markets.startswith("TOP_KRW_"):
        limit = int(markets.rsplit("_", 1)[-1])
        try:
            return loader.load_top_krw_markets(limit)
        except Exception:
            local = sorted(path.stem for path in (REPLAY_STORE_DIR / "v6_ohlcv" / "1d").glob("KRW-*.parquet"))
            return local[:limit] if local else ["KRW-BTC"]
    return [item.strip() for item in markets.split(",") if item.strip()]


def _loader_timeframe(timeframe: str) -> str:
    if timeframe == "4h":
        return "1h"
    return "1d" if timeframe in {"1d", "1w"} else timeframe


def _read_loader_frame(path: Path, timeframe: str, market: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    source_timeframe = _loader_timeframe(timeframe)
    frame = normalize_ohlcv(pd.read_parquet(path), source_timeframe, market)
    if timeframe != source_timeframe:
        return resample_ohlcv(frame, timeframe, market)
    return frame


def _coverage_row(market: str, timeframe: str, frame: pd.DataFrame, status: str) -> dict[str, Any]:
    if frame.empty:
        return {
            "market": market,
            "timeframe": timeframe,
            "candles": 0,
            "earliest_available_time": None,
            "latest_time": None,
            "actual_months_available": 0.0,
            "status": status,
            "api_limit_stop_reason": None,
        }
    earliest = pd.to_datetime(frame["time"]).min()
    latest = pd.to_datetime(frame["time"]).max()
    return {
        "market": market,
        "timeframe": timeframe,
        "candles": int(len(frame)),
        "earliest_available_time": str(earliest),
        "latest_time": str(latest),
        "actual_months_available": max(0.0, (latest - earliest).days / 30.4375),
        "status": status,
        "api_limit_stop_reason": None,
    }


def _summary(markets: str, selected_markets: list[str], timeframes: list[str], max_days: int, rows: list[dict], stop_reasons: dict[str, str]) -> dict[str, Any]:
    non_empty = [row for row in rows if row["candles"] > 0]
    earliest = min((row["earliest_available_time"] for row in non_empty if row["earliest_available_time"]), default=None)
    latest = max((row["latest_time"] for row in non_empty if row["latest_time"]), default=None)
    return {
        "schema_version": "walk_forward_archive_v1",
        "markets_requested": markets,
        "markets": selected_markets,
        "market_count": len(selected_markets),
        "timeframes": timeframes,
        "max_lookback_days": max_days,
        "earliest_available_time": earliest,
        "latest_time": latest,
        "rows": rows,
        "missing_market_count": len({row["market"] for row in rows if row["candles"] == 0}),
        "api_limit_stop_reason": stop_reasons or None,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_running_summary(
    markets: str,
    selected_markets: list[str],
    requested: list[str],
    max_lookback_days: int,
    rows: list[dict],
    stop_reasons: dict[str, str],
    archive_dir: str | Path,
) -> None:
    partial = _summary(markets, selected_markets, requested, max_lookback_days, rows, stop_reasons)
    partial["archive_status"] = "RUNNING_PARTIAL"
    _write(Path("docs/reports/latest_historical_archive_summary.json"), partial)
    _write(Path(archive_dir) / "latest_historical_archive_summary.json", partial)
