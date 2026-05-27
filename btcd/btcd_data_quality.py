from __future__ import annotations

from pathlib import Path
from typing import Any

from btcd.btcd_storage import latest_btcd_record
from btcd.global_btcd_history_loader import load_global_btcd_history


def build_v67_global_btcd_quality(
    history_path: str | Path = "data/external/btc_dominance_history.csv",
) -> dict[str, Any]:
    history, quality = load_global_btcd_history(history_path)
    current = latest_btcd_record("coinpaprika")
    possible = bool(quality.get("available") and quality.get("data_quality") == "GOOD")
    return {
        "schema_version": "v67_global_btcd_data_quality_v1",
        "data_sources": {
            "coinpaprika_current": _current_quality(current, "coinpaprika"),
            "coingecko_current": {"available": False, "period": "current only", "coverage": "not fetched by default", "notes": "Available as fallback client; not used for official backtest source."},
            "coinmarketcap_current": {"available": False, "period": "current only", "coverage": "requires CMC_API_KEY", "notes": "API key required; key is never printed."},
            "global_btcd_historical_csv": quality,
            "historical_api": {"available": False, "period": "unavailable", "coverage": "0%", "notes": "No configured paid historical API source."},
        },
        "full_period_validation_possible": possible,
        "reason": "Global BTCD historical data is available and GOOD." if possible else "Global BTCD historical CSV/API is unavailable or insufficient. Fake history was not generated.",
        "missing_data": [] if possible else ["data/external/btc_dominance_history.csv"],
        "fallback_used": False,
        "fake_data_generated": False,
        "historical_rows": len(history),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _current_quality(record: dict[str, Any] | None, source: str) -> dict[str, Any]:
    if not record:
        return {"available": False, "period": "current only", "coverage": "not collected", "notes": f"{source} current value not cached yet."}
    return {
        "available": record.get("dominance") is not None,
        "period": "current only",
        "coverage": str(record.get("fetched_at")),
        "notes": f"{source} current collector cache value. Current values are not used as fake history.",
        "dominance": record.get("dominance"),
    }
