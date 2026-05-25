from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class GlobalBTCDFEature:
    timestamp: str
    btc_dominance_pct: float | None
    btcd_delta_1d: float | None
    btcd_delta_7d: float | None
    btcd_delta_30d: float | None
    btcd_slope_7d: float | None
    btcd_slope_30d: float | None
    btcd_zscore_90d: float | None
    btcd_regime: str
    source: str
    lookahead_check: str = "PASS"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UpbitBTCFlowFeature:
    timestamp: str
    upbit_btc_flow_dominance_pct: float | None
    flow_delta_1d: float | None
    flow_delta_7d: float | None
    flow_zscore_30d: float | None
    flow_regime: str
    alt_volume_breadth: float | None
    source: str = "upbit_ohlcv"
    lookahead_check: str = "PASS"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BearRegimeComposite:
    bear_transition_score: int
    bear_state: str
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BTCDDecisionFeature:
    timestamp: str
    global_btcd: GlobalBTCDFEature
    upbit_flow: UpbitBTCFlowFeature
    bear: BearRegimeComposite
    used_future_data: bool = False
    lookahead_check: str = "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "global_btcd": self.global_btcd.as_dict(),
            "upbit_flow": self.upbit_flow.as_dict(),
            "bear": self.bear.as_dict(),
            "used_future_data": self.used_future_data,
            "lookahead_check": self.lookahead_check,
        }

