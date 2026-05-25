from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MAValue:
    timeframe: str
    ma_type: str
    period: int
    value: float | None
    slope_pct: float | None = None
    meaning: str = ""


@dataclass(frozen=True)
class MAFeature:
    market: str
    feature_time: str
    ma_timeframe: str
    close: float
    values: dict[str, MAValue] = field(default_factory=dict)
    states: list[str] = field(default_factory=list)
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    used_future_data: bool = False
    lookahead_check: str = "PASS"

    def has(self, state: str) -> bool:
        return state in self.states

    def as_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "feature_time": self.feature_time,
            "ma_timeframe": self.ma_timeframe,
            "close": self.close,
            "states": list(self.states),
            "score": self.score,
            "reasons": list(self.reasons),
            "used_future_data": self.used_future_data,
            "lookahead_check": self.lookahead_check,
            "values": {
                key: {
                    "timeframe": value.timeframe,
                    "ma_type": value.ma_type,
                    "period": value.period,
                    "value": value.value,
                    "slope_pct": value.slope_pct,
                    "meaning": value.meaning,
                }
                for key, value in self.values.items()
            },
        }
