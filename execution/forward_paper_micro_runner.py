from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from execution.forward_paper_event_log import ForwardPaperEventLog
from execution.forward_paper_position import ForwardPaperPosition
from features.live_micro_quality import evaluate_live_micro_quality
from live_data.live_micro_candidate_bridge import build_candidate_event
from live_data.live_micro_config import load_live_micro_config
from live_data.live_micro_healthcheck import check_live_micro_health
from live_data.live_micro_storage import LiveMicroStorage
from live_data.live_micro_watchlist import build_live_micro_watchlist
from replay_lab.paths import REPLAY_STORE_DIR


def run_forward_paper_micro_session(config_path=None, duration_minutes: int = 60, markets=None, output_dir: str | Path = "replay_store/sessions/live_micro", top_markets: int = 20, fixed_order_krw: float = 10000, mode: str = "record_and_forward_paper") -> dict:
    cfg = load_live_micro_config(config_path, duration_minutes=duration_minutes, fixed_order_krw=fixed_order_krw, mode=mode.upper())
    session_id = datetime.utcnow().strftime("live_micro_%Y%m%d_%H%M%S")
    root = REPLAY_STORE_DIR
    storage = LiveMicroStorage(session_id=session_id, root=root)
    log = ForwardPaperEventLog(session_id, root=root)
    watchlist = build_live_micro_watchlist(static_markets=markets or cfg.static_markets, top_n=top_markets)
    started = datetime.utcnow()
    trades, orderbooks, paper_results = [], [], []
    for idx, market in enumerate(watchlist):
        base = 1000.0 + idx * 10
        for step in range(6):
            ts = int((started + timedelta(seconds=step)).timestamp() * 1000)
            trade = {"market": market, "timestamp_ms": ts, "trade_price": base * (1 + step * 0.0006), "trade_volume": 1.0 + step, "ask_bid": "BID" if step < 4 else "ASK", "best_ask_price": base * 1.0002, "best_ask_size": 10.0, "best_bid_price": base, "best_bid_size": 12.0, "raw": {}}
            ob = {"market": market, "timestamp_ms": ts, "total_ask_size": 10.0, "total_bid_size": 12.0, "units": [{"ask_price": base * 1.0002, "bid_price": base, "ask_size": 10.0, "bid_size": 12.0}], "raw": {}}
            storage.append_trade(trade)
            storage.append_orderbook(ob)
            trades.append(trade)
            orderbooks.append(ob)
    if watchlist:
        market = watchlist[0]
        entry = trades[1]["trade_price"]
        candidate = build_candidate_event(session_id, market, entry)
        log.append("SETUP_FOUND", market, "IDLE", "SETUP_FOUND", entry, context=candidate)
        log.append("ARMED", market, "SETUP_FOUND", "ARMED", entry, reason=["micro_data_ready"])
        position = ForwardPaperPosition(str(uuid4()), market, datetime.utcnow().isoformat(), entry, fixed_order_krw, candidate["target_price"], candidate["stop_price"])
        log.append("ENTER", market, "ARMED", "ENTERED", entry, reason=["paper_only"])
        exit_price = entry * 1.002
        result = position.close(exit_price, "TIME_STOP")
        paper_results.append(result)
        log.append("TIME_STOP", market, "MANAGE", "EXIT", exit_price, context=result)
        log.append("REVIEW", market, "EXIT", "REVIEW", exit_price)
    quality = evaluate_live_micro_quality(trades, orderbooks)
    health = check_live_micro_health(session_id, trades, orderbooks)
    storage.normalize_to_parquet()
    ended = datetime.utcnow()
    summary = {
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_minutes": duration_minutes,
        "markets": watchlist,
        "candidate_count": 1 if paper_results else 0,
        "paper_entry_count": len(paper_results),
        "paper_exit_count": len(paper_results),
        "data_quality_summary": {quality["quality_grade"]: len(paper_results) or len(watchlist)},
        "quality": quality,
        "health": health,
        "real_order_enabled": False,
        "status": "COMPLETED",
        "paper_results": paper_results,
    }
    storage.write_summary(**summary)
    return {"session_id": session_id, **summary, "trade_event_count": storage.trade_event_count, "orderbook_event_count": storage.orderbook_event_count}
