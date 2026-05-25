from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from market_data.ohlcv_store import OHLCVStore
from mtf.daily_trend_analyzer import analyze_daily_trend
from mtf.h1_setup_context import analyze_h1_setup_context
from mtf.h4_structure_analyzer import analyze_h4_structure
from mtf.mtf_schema import MTFContext
from mtf.weekly_trend_analyzer import analyze_weekly_trend


def build_v6_mtf_context(markets: str = "TOP_KRW_50", store: OHLCVStore | None = None) -> dict[str, Any]:
    store = store or OHLCVStore()
    selected = _resolve_markets(markets, store)
    rows = []
    for market in selected:
        weekly = analyze_weekly_trend(store.load("1w", market))
        daily = analyze_daily_trend(store.load("1d", market))
        h4 = analyze_h4_structure(store.load("4h", market))
        h1 = analyze_h1_setup_context(store.load("1h", market))
        score = weekly["score"] * 0.25 + daily["score"] * 0.3 + h4["score"] * 0.25 + h1["score"] * 0.2
        risk_regime = "RISK_OFF" if weekly["weekly_trend"] == "DOWN" and daily["daily_trend"] == "DOWN" else "RISK_ON" if score >= 55 else "SELECTIVE"
        rows.append(
            MTFContext(
                market=market,
                weekly_trend=weekly["weekly_trend"],
                daily_trend=daily["daily_trend"],
                h4_structure=h4["h4_structure"],
                h1_setup_bias=h1["h1_setup_bias"],
                mtf_score=float(score),
                risk_regime=risk_regime,
            ).to_dict()
        )
    summary = {
        "schema_version": "v6",
        "market_count": len(rows),
        "contexts": rows,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(Path("replay_store/v6_mtf/latest_v6_mtf_summary.json"), summary)
    _write(Path("docs/reports/latest_v6_mtf_summary.json"), summary)
    return summary


def _resolve_markets(markets: str, store: OHLCVStore) -> list[str]:
    if markets.startswith("TOP_KRW_"):
        limit = int(markets.rsplit("_", 1)[-1]) if markets.rsplit("_", 1)[-1].isdigit() else 50
        return store.list_markets("1d")[:limit] or store.list_markets("1m")[:limit]
    return [item.strip() for item in markets.split(",") if item.strip()]


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
