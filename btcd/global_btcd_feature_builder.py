from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from btcd.btcd_regime_detector import detect_global_btcd_regime
from btcd.global_btcd_history_loader import load_global_btcd_history


class GlobalBTCDHistoryFeatureStore:
    def __init__(self, history_path: str | Path = "data/external/btc_dominance_history.csv") -> None:
        self.frame, self.quality = load_global_btcd_history(history_path)

    def feature_for(self, decision_time: str) -> dict[str, Any]:
        dt = pd.Timestamp(decision_time)
        if self.frame.empty:
            return {
                "timestamp": str(dt),
                "source": "unavailable",
                "btc_dominance_pct": None,
                "btcd_regime": "BTCD_UNAVAILABLE",
                "data_quality": "UNAVAILABLE",
                "lookahead_check": "PASS",
            }
        frame = self.frame[self.frame["timestamp"] <= dt]
        if frame.empty:
            return {
                "timestamp": str(dt),
                "source": "csv",
                "btc_dominance_pct": None,
                "btcd_regime": "BTCD_UNAVAILABLE",
                "data_quality": "UNAVAILABLE",
                "lookahead_check": "PASS",
            }
        current = frame.iloc[-1]
        value = float(current["btc_dominance_pct"])
        d1 = _delta(frame, value, 1)
        d7 = _delta(frame, value, 7)
        d30 = _delta(frame, value, 30)
        ma7 = frame["btc_dominance_pct"].tail(7).mean()
        ma30 = frame["btc_dominance_pct"].tail(30).mean()
        std90 = frame["btc_dominance_pct"].tail(90).std()
        mean90 = frame["btc_dominance_pct"].tail(90).mean()
        z90 = (value - mean90) / std90 if std90 and std90 > 0 else 0.0
        feature_time = pd.Timestamp(current["timestamp"])
        return {
            "timestamp": str(feature_time),
            "source": str(current.get("source", "csv")),
            "btc_dominance_pct": value,
            "btcd_delta_24h": d1,
            "btcd_delta_7d": d7,
            "btcd_delta_30d": d30,
            "btcd_ma_7d": float(ma7),
            "btcd_ma_30d": float(ma30),
            "btcd_slope_7d": d7 / 7.0 if d7 is not None else None,
            "btcd_slope_30d": d30 / 30.0 if d30 is not None else None,
            "btcd_zscore_90d": float(z90),
            "btcd_regime": detect_global_btcd_regime(d7, d30, z90),
            "data_quality": self.quality.get("data_quality", "PARTIAL"),
            "lookahead_check": "PASS" if feature_time <= dt else "FAIL",
        }


def _delta(frame: pd.DataFrame, current_value: float, periods: int) -> float | None:
    if len(frame) <= periods:
        return None
    prior = float(frame.iloc[-periods - 1]["btc_dominance_pct"])
    return current_value - prior
