from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.paths import REPLAY_STORE_DIR
from market_data.ohlcv_store import OHLCVStore, empty_ohlcv, normalize_ohlcv
from market_data.timeframe_resampler import resample_ohlcv


SUPPORTED_TIMEFRAMES = ["1w", "1d", "4h", "1h", "15m", "5m", "1m"]


def collect_v6_ohlcv(
    markets: str = "TOP_KRW_50",
    months: int = 12,
    timeframes: str = "1w,1d,4h,1h,15m,5m,1m",
    store: OHLCVStore | None = None,
) -> dict[str, Any]:
    store = store or OHLCVStore()
    requested = [_normalize_timeframe(item.strip()) for item in timeframes.split(",") if item.strip()]
    selected_markets = _resolve_markets(markets)
    source_root = REPLAY_STORE_DIR / "normalized" / "candles_1m"
    summary_rows = []
    since = datetime.utcnow() - timedelta(days=max(1, months) * 31)

    for market in selected_markets:
        base = _load_local_1m(source_root / f"{market}.parquet", market, since)
        status = "LOCAL_CACHE"
        if base.empty:
            base = _fetch_recent_1m(market, since)
            status = "UPBIT_PUBLIC_RECENT" if not base.empty else "DATA_MISSING"
        for timeframe in requested:
            if timeframe not in SUPPORTED_TIMEFRAMES:
                continue
            frame = base if timeframe == "1m" else resample_ohlcv(base, timeframe, market)
            if not frame.empty:
                store.save(timeframe, market, frame)
            summary_rows.append(
                {
                    "timeframe": timeframe,
                    "market": market,
                    "candles": int(len(frame)),
                    "status": status if len(frame) else "MISSING",
                }
            )

    by_timeframe = {}
    for timeframe in requested:
        rows = [row for row in summary_rows if row["timeframe"] == timeframe]
        by_timeframe[timeframe] = {
            "markets": sum(1 for row in rows if row["candles"] > 0),
            "candles": sum(int(row["candles"]) for row in rows),
            "status": "OK" if any(row["candles"] > 0 for row in rows) else "MISSING",
        }
    summary = {
        "schema_version": "v6",
        "markets_requested": markets,
        "markets": selected_markets,
        "months": months,
        "timeframes": requested,
        "by_timeframe": by_timeframe,
        "rows": summary_rows,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(Path("docs/reports/latest_v6_ohlcv_summary.json"), summary)
    store.write_summary(summary)
    return summary


def _resolve_markets(markets: str) -> list[str]:
    if not markets or markets.startswith("TOP_KRW_"):
        limit = int(markets.rsplit("_", 1)[-1]) if markets.rsplit("_", 1)[-1].isdigit() else 50
        local = sorted(path.stem for path in (REPLAY_STORE_DIR / "normalized" / "candles_1m").glob("KRW-*.parquet"))
        ordered = ["KRW-BTC", "KRW-ETH"] + [market for market in local if market not in {"KRW-BTC", "KRW-ETH"}]
        if ordered:
            return ordered[:limit]
        try:
            return HistoricalLoader().load_top_krw_markets(limit)
        except Exception:
            return ["KRW-BTC"]
    return [item.strip() for item in markets.split(",") if item.strip()]


def _normalize_timeframe(value: str) -> str:
    # PowerShell can occasionally pass an unquoted 1d-like token oddly through wrappers.
    return "1d" if value in {"1", "d", "day", "1day"} else value


def _load_local_1m(path: Path, market: str, since: datetime) -> pd.DataFrame:
    if not path.exists():
        return empty_ohlcv()
    data = normalize_ohlcv(pd.read_parquet(path), "1m", market)
    return data[data["time"] >= pd.Timestamp(since)].reset_index(drop=True)


def _fetch_recent_1m(market: str, since: datetime) -> pd.DataFrame:
    end = datetime.utcnow()
    start = max(since, end - timedelta(days=7))
    try:
        path = HistoricalLoader().load_candles(market, "1m", start, end)
        return normalize_ohlcv(pd.read_parquet(path), "1m", market)
    except Exception:
        return empty_ohlcv()


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
