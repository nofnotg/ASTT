from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BTCDOMIndexCandle:
    timestamp: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "uploaded_csv"
    source_type: str = "BTCDOM_INDEX_PROXY"
    is_percentage: bool = False
    lookahead_safe: bool = True
