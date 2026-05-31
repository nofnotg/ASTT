from __future__ import annotations

from typing import Any


def build_ltf_backfill_plan(coverage: dict[str, Any]) -> dict[str, Any]:
    missing = [row for row in coverage.get("trade_rows", []) if row.get("uncovered")]
    markets = sorted({str(row.get("market")) for row in missing if row.get("market")})
    return {
        "missing_trade_count": len(missing),
        "markets_to_backfill": markets,
        "timeframes": ["1m", "5m", "15m"],
        "fake_data_generated": False,
        "next_action": "collect_verified_lower_timeframe_data" if missing else "coverage_ready",
    }
