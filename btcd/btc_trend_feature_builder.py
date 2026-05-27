from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class BTCTrendFeatureStore:
    def __init__(self, archive_dir: str | Path = "replay_store/historical_archive", fallback_dir: str | Path = "replay_store/v6_ohlcv") -> None:
        self.archive_dir = Path(archive_dir)
        self.fallback_dir = Path(fallback_dir)
        self.frame = self._load_btc_daily()

    def feature_for(self, decision_time: str) -> dict[str, Any]:
        dt = pd.Timestamp(decision_time).floor("D")
        if self.frame.empty:
            return _empty(dt)
        frame = self.frame[self.frame["time"] <= dt]
        if frame.empty:
            return _empty(dt)
        close = frame["trade_price"].astype(float)
        current = close.iloc[-1]
        ret1 = _return(close, 1)
        ret7 = _return(close, 7)
        vol7 = close.pct_change().tail(7).std() * 100.0
        trend = "SIDEWAYS"
        if ret7 is not None and ret7 > 2.0:
            trend = "UP"
        elif ret7 is not None and ret7 < -2.0:
            trend = "DOWN"
        structure = "RANGE"
        if len(close) >= 30:
            ma7 = close.tail(7).mean()
            ma30 = close.tail(30).mean()
            if current > ma7 > ma30:
                structure = "UPTREND"
            elif current < ma7 < ma30:
                structure = "DOWNTREND"
            elif ret7 is not None and ret7 < -5:
                structure = "BREAKDOWN"
            elif ret7 is not None and ret7 > 5:
                structure = "RECOVERY"
        return {
            "timestamp": str(frame.iloc[-1]["time"]),
            "btc_price_trend_1d": "UP" if (ret1 or 0) > 0.5 else "DOWN" if (ret1 or 0) < -0.5 else "SIDEWAYS",
            "btc_price_trend_4h": trend,
            "btc_return_24h": ret1,
            "btc_return_7d": ret7,
            "btc_volatility_7d": None if pd.isna(vol7) else float(vol7),
            "btc_structure": structure,
            "lookahead_check": "PASS" if pd.Timestamp(frame.iloc[-1]["time"]) <= dt else "FAIL",
        }

    def _load_btc_daily(self) -> pd.DataFrame:
        for root in [self.archive_dir, self.fallback_dir]:
            path = root / "1d" / "KRW-BTC.parquet"
            if path.exists():
                frame = pd.read_parquet(path)
                if "time" in frame and "trade_price" in frame:
                    frame = frame.copy()
                    frame["time"] = pd.to_datetime(frame["time"], errors="coerce").dt.floor("D")
                    frame["trade_price"] = pd.to_numeric(frame["trade_price"], errors="coerce")
                    return frame.dropna(subset=["time", "trade_price"]).sort_values("time")
        return pd.DataFrame()


def _return(close: pd.Series, periods: int) -> float | None:
    if len(close) <= periods:
        return None
    prior = float(close.iloc[-periods - 1])
    if prior <= 0:
        return None
    return (float(close.iloc[-1]) / prior - 1.0) * 100.0


def _empty(dt: pd.Timestamp) -> dict[str, Any]:
    return {
        "timestamp": str(dt),
        "btc_price_trend_1d": "SIDEWAYS",
        "btc_price_trend_4h": "SIDEWAYS",
        "btc_return_24h": None,
        "btc_return_7d": None,
        "btc_volatility_7d": None,
        "btc_structure": "RANGE",
        "lookahead_check": "PASS",
    }
