from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.event_clip_store import read_jsonl


SETUP_TYPES = [
    "PULLBACK_RECLAIM",
    "RANGE_BREAKOUT",
    "ROLE_FLIP_SUPPORT",
    "COMPRESSION_EXPANSION",
    "VWAP_RECLAIM_WITH_VOLUME",
    "LEADER_ROTATION_SURGE",
]


def build_setup_candidates_v5r3(sessions_dir: str | Path = "replay_store/sessions", initial_cash_krw: float = 500000) -> dict[str, Any]:
    regime = _read(REPLAY_STORE_DIR / "market_regime" / "latest_market_regime_summary.json")
    candidates = []
    rejected = Counter()
    for clip in sorted((REPLAY_STORE_DIR / "timing_clips").glob("*/*/clip_meta.json")):
        meta = _read(clip)
        trades = read_jsonl(clip.parent / "trades.jsonl")
        orderbooks = read_jsonl(clip.parent / "orderbooks.jsonl")
        candidate = _candidate_from_clip(meta, trades, orderbooks, regime, initial_cash_krw)
        if candidate["setup_score"] >= 50 and candidate["data_quality"] != "LOW":
            candidates.append(candidate)
        else:
            rejected.update(candidate["reject_reasons"] or ["SETUP_SCORE_LOW"])
    counts = Counter(row["setup_type"] for row in candidates)
    grade_counts = Counter(row["setup_grade"] for row in candidates)
    by_setup_type = {}
    for setup_type in counts:
        rows = [row for row in candidates if row["setup_type"] == setup_type]
        by_setup_type[setup_type] = {
            "count": len(rows),
            "avg_score": sum(float(row.get("setup_score", 0.0)) for row in rows) / len(rows),
            "grade_counts": dict(Counter(row.get("setup_grade", "C") for row in rows)),
        }
    summary = {
        "schema_version": "v5r3",
        "candidate_count": len(candidates),
        "setup_counts": dict(counts),
        "by_setup_type": by_setup_type,
        "grade_counts": dict(grade_counts),
        "rejected_counts": dict(rejected),
        "initial_cash_krw": float(initial_cash_krw),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "candidates": candidates,
    }
    _write(REPLAY_STORE_DIR / "setup_candidates" / "latest_setup_candidate_summary.json", summary)
    _write(Path("docs/reports/latest_setup_candidate_summary.json"), summary)
    return summary


def _candidate_from_clip(meta: dict[str, Any], trades: list[dict[str, Any]], orderbooks: list[dict[str, Any]], regime: dict[str, Any], initial_cash_krw: float) -> dict[str, Any]:
    market = meta.get("market", "")
    event_type = meta.get("event_type", "")
    event_time = int(meta.get("event_time_ms", 0) or 0)
    pre = [row for row in trades if int(row.get("timestamp_ms", 0) or 0) <= event_time] or trades[: max(1, min(10, len(trades)))]
    prices = [float(row.get("trade_price", 0.0) or 0.0) for row in pre if float(row.get("trade_price", 0.0) or 0.0) > 0]
    buy_ratio = sum(1 for row in pre if row.get("ask_bid") == "BID") / len(pre) if pre else 0.0
    volume_krw = sum(float(row.get("trade_volume", 0.0) or 0.0) * float(row.get("trade_price", 0.0) or 0.0) for row in pre)
    price_response_pct = (prices[-1] - prices[0]) / prices[0] * 100 if len(prices) > 1 and prices[0] else 0.0
    spread_pct = _spread_pct(orderbooks)
    depth_3_level_krw = _depth_krw(orderbooks)
    setup_type = _setup_type(event_type, buy_ratio, price_response_pct, volume_krw)
    rr = _risk_reward(price_response_pct, spread_pct, depth_3_level_krw)
    target_space_pct = max(0.35, abs(price_response_pct) * 2 + 0.35)
    score = _score(setup_type, buy_ratio, volume_krw, price_response_pct, spread_pct, depth_3_level_krw, regime)
    grade = _grade(score)
    reject_reasons = []
    if spread_pct > 0.35:
        reject_reasons.append("SPREAD_TOO_WIDE")
    if depth_3_level_krw < 300000:
        reject_reasons.append("DEPTH_TOO_THIN")
    if not regime.get("long_allowed", False):
        reject_reasons.append("REGIME_BLOCKED")
    if score < 50:
        reject_reasons.append("SETUP_SCORE_LOW")
    return {
        "candidate_id": f"{meta.get('clip_id', market)}_setup_v5r3",
        "clip_id": meta.get("clip_id", ""),
        "event_id": meta.get("event_id", ""),
        "market": market,
        "event_type": event_type,
        "event_time_ms": event_time,
        "setup_type": setup_type,
        "setup_score": score,
        "setup_grade": grade,
        "regime": regime.get("regime", "NO_TRADE"),
        "buy_trade_ratio": buy_ratio,
        "pre_trade_count": len(pre),
        "volume_krw": volume_krw,
        "price_response_pct": price_response_pct,
        "spread_pct": spread_pct,
        "depth_3_level_krw": depth_3_level_krw,
        "risk_reward": rr,
        "target_space_pct": target_space_pct,
        "allocation_hint_pct": {"B": 20, "A": 40, "S": 60}.get(grade, 0),
        "data_quality": "LOW" if not trades or not orderbooks else meta.get("quality", "PARTIAL"),
        "reject_reasons": reject_reasons,
        "real_order_enabled": False,
    }


def _setup_type(event_type: str, buy_ratio: float, price_response_pct: float, volume_krw: float) -> str:
    if event_type == "ORDERFLOW_SHIFT" and buy_ratio >= 0.55:
        return "PULLBACK_RECLAIM"
    if event_type == "RANGE_TOUCH":
        return "RANGE_BREAKOUT"
    if event_type == "VOLUME_SPIKE":
        return "VWAP_RECLAIM_WITH_VOLUME"
    if event_type == "MARKET_RANK_SURGE" and volume_krw >= 500000:
        return "LEADER_ROTATION_SURGE"
    if abs(price_response_pct) <= 0.08 and volume_krw >= 300000:
        return "COMPRESSION_EXPANSION"
    return "ROLE_FLIP_SUPPORT"


def _score(setup_type: str, buy_ratio: float, volume_krw: float, price_response_pct: float, spread_pct: float, depth_krw: float, regime: dict[str, Any]) -> float:
    score = 28.0
    score += {"PULLBACK_RECLAIM": 18, "RANGE_BREAKOUT": 16, "ROLE_FLIP_SUPPORT": 12, "COMPRESSION_EXPANSION": 14, "VWAP_RECLAIM_WITH_VOLUME": 16, "LEADER_ROTATION_SURGE": 10}.get(setup_type, 0)
    score += max(0.0, (buy_ratio - 0.45) * 80)
    score += min(16.0, volume_krw / 100000)
    score += min(10.0, abs(price_response_pct) * 20)
    score += 10 if depth_krw >= 500000 else 0
    score -= max(0.0, spread_pct - 0.12) * 60
    score += 8 if regime.get("regime") == "RISK_ON" else 4 if regime.get("regime") == "SELECTIVE_ALT" else -24
    return float(max(0.0, min(100.0, score)))


def _grade(score: float) -> str:
    if score >= 78:
        return "S"
    if score >= 68:
        return "A"
    if score >= 55:
        return "B"
    return "C"


def _risk_reward(price_response_pct: float, spread_pct: float, depth_krw: float) -> float:
    cost = max(0.15, spread_pct + 0.10)
    target = max(0.35, abs(price_response_pct) * 2 + (0.25 if depth_krw >= 500000 else 0.0))
    return float(target / cost if cost else 0.0)


def _spread_pct(orderbooks: list[dict[str, Any]]) -> float:
    if not orderbooks:
        return 0.2
    units = orderbooks[0].get("units") or []
    if not units:
        return 0.2
    ask = float(units[0].get("ask_price", 0.0) or 0.0)
    bid = float(units[0].get("bid_price", 0.0) or 0.0)
    mid = (ask + bid) / 2 if ask and bid else 0.0
    return (ask - bid) / mid * 100 if mid else 0.2


def _depth_krw(orderbooks: list[dict[str, Any]]) -> float:
    if not orderbooks:
        return 0.0
    total = 0.0
    for unit in (orderbooks[0].get("units") or [])[:3]:
        total += float(unit.get("ask_price", 0.0) or 0.0) * float(unit.get("ask_size", 0.0) or 0.0)
    return total


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
