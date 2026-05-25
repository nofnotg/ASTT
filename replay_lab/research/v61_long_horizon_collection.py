from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from market_data.ohlcv_coverage_reporter import build_ohlcv_coverage
from market_data.upbit_long_ohlcv_collector import collect_long_ohlcv


def run_v61_long_horizon_collection(markets: str, months: int, timeframes: str) -> dict[str, Any]:
    summary = collect_long_ohlcv(markets, months, timeframes)
    coverage = build_ohlcv_coverage("replay_store/v6_ohlcv", months)
    payload = {**summary, "coverage": coverage, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v61_collection_summary.json", payload)
    return payload


def _write(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
