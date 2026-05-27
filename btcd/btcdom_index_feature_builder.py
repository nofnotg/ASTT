from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from btcd.btcdom_index_regime_classifier import classify_btcdom_index_regime


class BTCDOMIndexFeatureStore:
    def __init__(self, processed_dir: str | Path = "data/processed") -> None:
        self.processed_dir = Path(processed_dir)
        self.frames = {tf: self._load(tf) for tf in ("1h", "4h", "1d")}

    def data_quality(self) -> dict[str, Any]:
        available = {tf: not frame.empty for tf, frame in self.frames.items()}
        starts = [frame["timestamp"].min() for frame in self.frames.values() if not frame.empty]
        ends = [frame["timestamp"].max() for frame in self.frames.values() if not frame.empty]
        return {
            "available": all(available.values()),
            "timeframes": available,
            "common_coverage_start": max(starts).isoformat() if starts else None,
            "common_coverage_end": min(ends).isoformat() if ends else None,
            "data_quality": "GOOD" if all(available.values()) else "PARTIAL",
        }

    def feature_for(self, decision_time: str) -> dict[str, Any]:
        decision = pd.Timestamp(decision_time)
        if decision.tzinfo is None:
            decision = decision.tz_localize("UTC")
        else:
            decision = decision.tz_convert("UTC")
        out: dict[str, Any] = {"decision_time": decision.isoformat(), "lookahead_check": "PASS"}
        for tf, frame in self.frames.items():
            row = self._last_closed(frame, decision)
            if row is None:
                out[f"btcdom_feature_time_{tf}"] = None
                out[f"btcdom_index_close_{tf}"] = None
                out["btcdom_data_quality"] = "GAP"
                out["lookahead_check"] = "FAIL"
                continue
            out[f"btcdom_feature_time_{tf}"] = row["timestamp"].isoformat()
            out[f"btcdom_index_close_{tf}"] = float(row["close"])
            if row["timestamp"] > decision:
                out["lookahead_check"] = "FAIL"
        daily = self.frames["1d"]
        latest = self._last_closed(daily, decision)
        if latest is None:
            out.update({"btcdom_regime": "UNAVAILABLE", "btcdom_data_quality": "UNAVAILABLE", "lookahead_check": "FAIL"})
            return out
        daily_until = daily[daily["timestamp"] <= latest["timestamp"]].copy()
        close = daily_until["close"].astype(float)
        out.update(
            {
                "btcdom_delta_1h": _delta(self.frames["1h"], decision, 1),
                "btcdom_delta_4h": _delta(self.frames["4h"], decision, 1),
                "btcdom_delta_24h": _delta(daily, decision, 1),
                "btcdom_delta_7d": _delta(daily, decision, 7),
                "btcdom_delta_30d": _delta(daily, decision, 30),
                "btcdom_ma_7d": float(close.tail(7).mean()) if len(close) >= 1 else 0.0,
                "btcdom_ma_30d": float(close.tail(30).mean()) if len(close) >= 1 else 0.0,
                "btcdom_slope_7d": _delta(daily, decision, 7) / 7.0,
                "btcdom_slope_30d": _delta(daily, decision, 30) / 30.0,
                "btcdom_zscore_90d": _zscore(close.tail(90)),
                "btcdom_data_quality": "GOOD",
            }
        )
        out["btcdom_regime"] = classify_btcdom_index_regime(out)
        return out

    def _load(self, timeframe: str) -> pd.DataFrame:
        path = self.processed_dir / f"btcdom_index_{timeframe}_normalized.csv"
        if not path.exists():
            return pd.DataFrame(columns=["timestamp", "close"])
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        return frame.dropna(subset=["timestamp", "close"]).sort_values("timestamp")

    def _last_closed(self, frame: pd.DataFrame, decision: pd.Timestamp) -> pd.Series | None:
        if frame.empty:
            return None
        eligible = frame[frame["timestamp"] <= decision]
        if eligible.empty:
            return None
        return eligible.iloc[-1]


def _delta(frame: pd.DataFrame, decision: pd.Timestamp, periods: int) -> float:
    eligible = frame[frame["timestamp"] <= decision] if not frame.empty else pd.DataFrame()
    if len(eligible) <= periods:
        return 0.0
    return float(eligible.iloc[-1]["close"]) - float(eligible.iloc[-1 - periods]["close"])


def _zscore(values: pd.Series) -> float:
    if len(values) < 2:
        return 0.0
    std = float(values.std())
    if std == 0:
        return 0.0
    return (float(values.iloc[-1]) - float(values.mean())) / std
