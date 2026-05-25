from __future__ import annotations

from typing import Any

from replay_lab.research.v6_ohlcv_collection import run_v6_ohlcv_collection


def collect_long_ohlcv(markets: str = "TOP_KRW_100", months: int = 36, timeframes: str = "1w,1d,4h,1h,15m,5m,1m") -> dict[str, Any]:
    summary = run_v6_ohlcv_collection(markets, months, timeframes)
    summary["schema_version"] = "v6.1"
    summary["requested_months"] = months
    summary["coverage_note"] = "Uses available public/local OHLCV cache; reports actual coverage separately."
    return summary
