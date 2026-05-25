from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from btcd.btcd_regime_detector import build_bear_composite, detect_global_btcd_regime
from btcd.btcd_schema import BTCDDecisionFeature, GlobalBTCDFEature, UpbitBTCFlowFeature
from btcd.global_btcd_loader import load_global_btcd
from btcd.upbit_btc_flow_dominance import build_upbit_btc_flow_dominance


class BTCDFeatureStore:
    def __init__(
        self,
        archive_dir: str | Path = "replay_store/historical_archive",
        fallback_dir: str | Path = "replay_store/v6_ohlcv",
        global_csv_path: str | Path = "data/external/btc_dominance.csv",
    ) -> None:
        self.archive_dir = Path(archive_dir)
        self.fallback_dir = Path(fallback_dir)
        self.global_frame, self.global_quality = load_global_btcd(global_csv_path)
        self.flow_frame, self.flow_quality = build_upbit_btc_flow_dominance(self.archive_dir, self.fallback_dir)

    def data_quality(self) -> dict[str, Any]:
        return {
            "global_btc_dominance": self.global_quality,
            "upbit_btc_flow_dominance_proxy": self.flow_quality,
        }

    def feature_for(
        self,
        decision_time: str,
        strategy_pf: float | None = None,
        drawdown_pct: float = 0.0,
        monthly_return_pct: float = 0.0,
    ) -> BTCDDecisionFeature:
        dt = pd.Timestamp(decision_time)
        global_feature = self._global_feature(dt)
        flow_feature = self._flow_feature(dt)
        bear = build_bear_composite(
            global_feature.btcd_regime,
            flow_feature.flow_regime,
            flow_feature.alt_volume_breadth,
            strategy_pf,
            drawdown_pct,
            monthly_return_pct,
        )
        used_future = global_feature.lookahead_check != "PASS" or flow_feature.lookahead_check != "PASS"
        return BTCDDecisionFeature(
            timestamp=str(dt),
            global_btcd=global_feature,
            upbit_flow=flow_feature,
            bear=bear,
            used_future_data=used_future,
            lookahead_check="FAIL" if used_future else "PASS",
        )

    def _global_feature(self, dt: pd.Timestamp) -> GlobalBTCDFEature:
        if self.global_frame.empty:
            return GlobalBTCDFEature(str(dt), None, None, None, None, None, None, None, "BTCD_UNAVAILABLE", "unavailable")
        frame = self.global_frame[self.global_frame["timestamp"] <= dt]
        if frame.empty:
            return GlobalBTCDFEature(str(dt), None, None, None, None, None, None, None, "BTCD_UNAVAILABLE", "csv")
        current = frame.iloc[-1]
        value = float(current["btc_dominance_pct"])
        d1 = _delta(frame, value, 1)
        d7 = _delta(frame, value, 7)
        d30 = _delta(frame, value, 30)
        mean90 = frame["btc_dominance_pct"].tail(90).mean()
        std90 = frame["btc_dominance_pct"].tail(90).std()
        z90 = (value - mean90) / std90 if std90 and std90 > 0 else 0.0
        return GlobalBTCDFEature(
            timestamp=str(current["timestamp"]),
            btc_dominance_pct=value,
            btcd_delta_1d=d1,
            btcd_delta_7d=d7,
            btcd_delta_30d=d30,
            btcd_slope_7d=d7 / 7.0 if d7 is not None else None,
            btcd_slope_30d=d30 / 30.0 if d30 is not None else None,
            btcd_zscore_90d=z90,
            btcd_regime=detect_global_btcd_regime(d7, d30, z90),
            source=str(current.get("source", "csv")),
            lookahead_check="PASS" if pd.Timestamp(current["timestamp"]) <= dt else "FAIL",
        )

    def _flow_feature(self, dt: pd.Timestamp) -> UpbitBTCFlowFeature:
        if self.flow_frame.empty:
            return UpbitBTCFlowFeature(str(dt), None, None, None, None, "BTC_FLOW_UNAVAILABLE", None, source="unavailable")
        frame = self.flow_frame[self.flow_frame["time"] <= dt.floor("D")]
        if frame.empty:
            return UpbitBTCFlowFeature(str(dt), None, None, None, None, "BTC_FLOW_UNAVAILABLE", None)
        row = frame.iloc[-1]
        return UpbitBTCFlowFeature(
            timestamp=str(row["time"]),
            upbit_btc_flow_dominance_pct=float(row.get("upbit_btc_flow_dominance_pct", 0.0)),
            flow_delta_1d=_safe_float(row.get("flow_delta_1d")),
            flow_delta_7d=_safe_float(row.get("flow_delta_7d")),
            flow_zscore_30d=_safe_float(row.get("flow_zscore_30d")),
            flow_regime=str(row.get("flow_regime", "BTC_FLOW_STABLE")),
            alt_volume_breadth=_safe_float(row.get("alt_volume_breadth")),
            lookahead_check="PASS" if pd.Timestamp(row["time"]) <= dt else "FAIL",
        )


def _delta(frame: pd.DataFrame, current_value: float, periods: int) -> float | None:
    if len(frame) <= periods:
        return None
    prior = float(frame.iloc[-periods - 1]["btc_dominance_pct"])
    return current_value - prior


def _safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

