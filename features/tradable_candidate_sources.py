from __future__ import annotations

import hashlib

from features.btc_market_context_features import btc_context_allows_momentum
from features.liquidity_context_features import liquidity_context_pass


TRADABLE_SOURCES = (
    "TRADABLE_VOLUME_BREAKOUT",
    "TRADABLE_ORDERFLOW_EXPANSION",
    "TRADABLE_COMPRESSION_BREAK",
    "TRADABLE_VWAP_TREND_RECLAIM",
    "BTC_ALIGNED_MOMENTUM",
)


def detect_tradable_candidate(snapshot: dict, source: str) -> dict | None:
    if not _base_pass(snapshot):
        return None
    checks = {
        "TRADABLE_VOLUME_BREAKOUT": _volume_breakout,
        "TRADABLE_ORDERFLOW_EXPANSION": _orderflow_expansion,
        "TRADABLE_COMPRESSION_BREAK": _compression_break,
        "TRADABLE_VWAP_TREND_RECLAIM": _vwap_trend_reclaim,
        "BTC_ALIGNED_MOMENTUM": _btc_aligned_momentum,
    }
    fn = checks.get(source)
    if not fn or not fn(snapshot):
        return None
    return _candidate(snapshot, source)


def detect_all_tradable_candidates(snapshot: dict, sources: list[str] | None = None) -> list[dict]:
    return [c for source in (sources or list(TRADABLE_SOURCES)) if (c := detect_tradable_candidate(snapshot, source))]


def _base_pass(snapshot: dict) -> bool:
    return bool(snapshot.get("tradable_prefilter_pass", False)) and liquidity_context_pass(snapshot) and float(snapshot.get("effective_return_pct", 0.0) or 0.0) > 0


def _volume_breakout(snapshot: dict) -> bool:
    return float(snapshot.get("volume_burst_60s_vs_600s", 0.0) or 0.0) >= 1.2 and float(snapshot.get("price_change_60s_pct", 0.0) or 0.0) >= 0


def _orderflow_expansion(snapshot: dict) -> bool:
    return float(snapshot.get("buy_trade_ratio_60s", 0.0) or 0.0) >= 0.52 and float(snapshot.get("orderbook_imbalance", 0.0) or 0.0) >= 0


def _compression_break(snapshot: dict) -> bool:
    return float(snapshot.get("range_compression_score", 0.0) or 0.0) >= 0.5 and _volume_breakout(snapshot)


def _vwap_trend_reclaim(snapshot: dict) -> bool:
    return float(snapshot.get("vwap_distance_pct", 0.0) or 0.0) >= 0 and _volume_breakout(snapshot)


def _btc_aligned_momentum(snapshot: dict) -> bool:
    return btc_context_allows_momentum(snapshot) and float(snapshot.get("price_change_60s_pct", 0.0) or 0.0) > 0


def _candidate(snapshot: dict, source: str) -> dict:
    key = f"{source}|{snapshot.get('market')}|{snapshot.get('timestamp_ms')}"
    return {
        "candidate_id": "tradable_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10],
        "market": snapshot.get("market", ""),
        "candidate_source": source,
        "candidate_time_ms": int(snapshot.get("timestamp_ms", 0) or 0),
        "reference_price": float(snapshot.get("last_price", 0.0) or 0.0),
        "expected_target_pct": max(0.45, float(snapshot.get("effective_return_pct", 0.0) or 0.0)),
        "expected_stop_pct": 0.35,
        "expected_hold_seconds": 300,
        "signal_grade_hint": "B",
        "evidence": snapshot,
        "tradable_prefilter_pass": True,
        "spread_pct": float(snapshot.get("spread_pct", 999.0) or 999.0),
        "depth_3_level_krw": float(snapshot.get("depth_3_level_krw", 0.0) or 0.0),
        "estimated_total_cost_pct": float(snapshot.get("estimated_total_cost_pct", 0.0) or 0.0),
        "effective_return_pct": float(snapshot.get("effective_return_pct", 0.0) or 0.0),
        "real_order_enabled": False,
        "research_mode": True,
    }
