from __future__ import annotations

import json
from datetime import datetime

from adapters.upbit_public_websocket import subscribe_upbit_ws
from live_capture.high_volatility_session_planner import plan_high_volatility_session
from live_capture.live_session_quality_guard import evaluate_live_session_quality
from live_capture.live_session_store import LiveSessionStore
from live_capture.market_volume_ranker import rank_top_krw_markets
from live_data.upbit_ws_message_normalizer import normalize_upbit_orderbook_message, normalize_upbit_trade_message
from replay_lab.paths import REPLAY_STORE_DIR


def collect_high_volatility_live_session_v5510(session_type: str = "RANDOM_CONTROL", duration_minutes: int = 30, top_markets: int = 20) -> dict:
    session_id = datetime.utcnow().strftime("live_v5510_%Y%m%d_%H%M%S")
    markets = rank_top_krw_markets(top_markets)
    if "KRW-BTC" not in markets:
        markets.insert(0, "KRW-BTC")
    root = REPLAY_STORE_DIR / "live_v5510" / session_id
    store = LiveSessionStore(root)
    counts = {"trade": 0, "orderbook": 0, "ticker": 0}
    started = datetime.utcnow()

    def on_raw(raw: dict) -> None:
        kind = raw.get("type")
        if kind == "trade":
            event = normalize_upbit_trade_message(raw)
            store.append_jsonl(f"trades/{event['market']}.jsonl", event)
            counts["trade"] += 1
        elif kind == "orderbook":
            event = normalize_upbit_orderbook_message(raw)
            store.append_jsonl(f"orderbooks/{event['market']}.jsonl", event)
            counts["orderbook"] += 1
        elif kind == "ticker":
            market = raw.get("code") or raw.get("market", "")
            store.append_jsonl(f"tickers/{market}.jsonl", {"data_source": "UPBIT_WS_LIVE", "type": "ticker", "market": market, "raw": raw})
            counts["ticker"] += 1

    warnings: list[str] = []
    result = subscribe_upbit_ws(markets, ["trade", "orderbook", "ticker"], max(1, duration_minutes * 60), on_raw)
    warnings.extend(result.get("warnings", []))
    ended = datetime.utcnow()
    quality = evaluate_live_session_quality(counts["trade"], counts["orderbook"], counts["ticker"], duration_minutes)
    warnings.extend(quality["warnings"])
    summary = {
        "session_id": session_id,
        "session_type": session_type,
        "plan": plan_high_volatility_session(session_type, duration_minutes, top_markets),
        "start_time_kst": started.isoformat(),
        "end_time_kst": ended.isoformat(),
        "duration_minutes": duration_minutes,
        "markets": markets,
        "trade_event_count": counts["trade"],
        "orderbook_event_count": counts["orderbook"],
        "ticker_event_count": counts["ticker"],
        "quality": quality["quality"],
        "data_source": "UPBIT_WS_LIVE",
        "real_order_enabled": False,
        "research_mode": True,
        "warnings": warnings,
    }
    store.write_json("session_summary.json", summary)
    latest = REPLAY_STORE_DIR / "live_v5510" / "latest_live_session_summary.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary
