from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TIMEFRAMES = ("1m", "5m", "15m")


@dataclass(frozen=True)
class LTFBar:
    market: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    timeframe: str = "1m"

    def as_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe,
        }
