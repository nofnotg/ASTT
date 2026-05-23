from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from features.ws_forward_candidate_features import build_ws_forward_candidate_features
from live_data.upbit_real_ws_session import run_upbit_real_ws_session
from replay_lab.paths import REPLAY_STORE_DIR


def run_forward_ws_session_v554(duration_minutes: int = 60, top_markets: int = 20, priority_strategies: list[str] | None = None, fixed_order_krw: float = 10000) -> dict:
    markets = _default_markets(top_markets)
    session = run_upbit_real_ws_session(markets, duration_seconds=duration_minutes * 60, include_trade=True, include_orderbook=True)
    candidates = build_ws_forward_candidate_features(session, priority_strategies)
    block_counts = Counter(row["primary_block_reason"] for row in candidates)
    summary = {
        "session_id": session["session_id"],
        "data_source": "UPBIT_WS",
        "duration_minutes": duration_minutes,
        "markets": markets,
        "trade_event_count": session.get("trade_event_count", 0),
        "orderbook_event_count": session.get("orderbook_event_count", 0),
        "candidate_count": len(candidates),
        "enter_count": sum(1 for row in candidates if row["entry_decision"] == "ENTER"),
        "wait_count": sum(1 for row in candidates if row["entry_decision"] == "WAIT"),
        "cancel_count": sum(1 for row in candidates if row["entry_decision"] == "CANCEL"),
        "block_reason_counts": dict(block_counts),
        "real_order_enabled": False,
        "fixed_order_krw": fixed_order_krw,
        "status": session.get("status", "FAILED"),
        "source_session": session,
        "candidate_events": candidates,
    }
    out = REPLAY_STORE_DIR / "sessions" / "forward_ws_v554" / summary["session_id"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "candidate_events.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary


def _default_markets(top_markets: int) -> list[str]:
    base = ["KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP", "KRW-DOGE", "KRW-ADA", "KRW-AVAX", "KRW-LINK", "KRW-SUI", "KRW-TRX"]
    return base[: max(1, min(top_markets, len(base)))]
