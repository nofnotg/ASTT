from __future__ import annotations

import hashlib
import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from tradable_winner.tradable_winner_prefilter import apply_tradable_winner_prefilter
from tradable_winner.tradable_winner_schema import TRADABLE_WINNER_TYPES, WINNER_TYPE_CONFIG


def detect_tradable_winners_from_recorded_sessions(
    sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions",
    initial_cash_krw: float = 500000,
    winner_types: list[str] | None = None,
) -> dict:
    requested = winner_types or list(TRADABLE_WINNER_TYPES)
    raw_root = REPLAY_STORE_DIR / "raw" / "upbit_ws"
    winners: list[dict] = []
    reject_counts: dict[str, int] = {}
    candidate_evaluated = 0
    for trade_file in raw_root.glob("*/*/trades/*.jsonl"):
        session_id = trade_file.parent.parent.name
        market = trade_file.stem
        orderbook_file = trade_file.parent.parent / "orderbooks" / f"{market}.jsonl"
        if not orderbook_file.exists():
            continue
        trades = _load_jsonl(trade_file, limit=6000)
        orderbooks = _load_jsonl(orderbook_file, limit=6000)
        if len(trades) < 2 or not orderbooks:
            continue
        sampled = _sample_trades(trades, step_ms=30_000)
        for start in sampled:
            for winner_type in requested:
                event = _detect_one_window(market, session_id, start, trades, orderbooks, winner_type)
                candidate_evaluated += 1
                if event["prefilter"]["prefilter_pass"]:
                    winners.append(event["winner"])
                else:
                    for reason in event["prefilter"]["reject_reasons"]:
                        reject_counts[reason] = reject_counts.get(reason, 0) + 1
    summary = _summarize(winners, reject_counts, candidate_evaluated)
    payload = {"summary": summary, "winners": winners}
    out = REPLAY_STORE_DIR / "tradable_winner" / "tradable_winners.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _detect_one_window(market: str, session_id: str, start: dict, trades: list[dict], orderbooks: list[dict], winner_type: str) -> dict:
    config = WINNER_TYPE_CONFIG[winner_type]
    start_ts = int(start.get("timestamp_ms", 0))
    end_min = start_ts + int(config["min_seconds"] * 1000)
    end_max = start_ts + int(config["max_seconds"] * 1000)
    future = [t for t in trades if end_min <= int(t.get("timestamp_ms", 0)) <= end_max]
    peak = max(future, key=lambda t: float(t.get("trade_price", 0.0) or 0.0), default=start)
    orderbook = _nearest_orderbook(orderbooks, start_ts)
    prefilter = apply_tradable_winner_prefilter(
        market,
        float(start.get("trade_price", 0.0) or 0.0),
        float(peak.get("trade_price", 0.0) or 0.0),
        orderbook,
        winner_type,
        trade_event_count=len(future),
        orderbook_event_count=len(orderbooks),
    )
    winner = {
        "winner_id": _id(market, session_id, start_ts, winner_type),
        "market": market,
        "winner_type": winner_type,
        "start_time_ms": start_ts,
        "peak_time_ms": int(peak.get("timestamp_ms", start_ts) or start_ts),
        "duration_seconds": max(0, int((int(peak.get("timestamp_ms", start_ts) or start_ts) - start_ts) / 1000)),
        "start_price": float(start.get("trade_price", 0.0) or 0.0),
        "peak_price": float(peak.get("trade_price", 0.0) or 0.0),
        "source_session_id": session_id,
        "source_data": "UPBIT_WS_RECORDED",
        "quality": "GOOD" if prefilter["prefilter_pass"] else "POOR",
        "reject_reasons": prefilter["reject_reasons"],
        **{k: v for k, v in prefilter.items() if k not in {"prefilter_pass", "reject_reasons"}},
    }
    return {"winner": winner, "prefilter": prefilter}


def _load_jsonl(path: Path, limit: int = 6000) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx >= limit:
                break
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _sample_trades(trades: list[dict], step_ms: int) -> list[dict]:
    sampled = []
    last = -1
    for trade in sorted(trades, key=lambda t: int(t.get("timestamp_ms", 0))):
        ts = int(trade.get("timestamp_ms", 0))
        if last < 0 or ts - last >= step_ms:
            sampled.append(trade)
            last = ts
    return sampled


def _nearest_orderbook(orderbooks: list[dict], ts: int) -> dict:
    return min(orderbooks, key=lambda row: abs(int(row.get("timestamp_ms", 0)) - ts), default={})


def _id(market: str, session_id: str, ts: int, winner_type: str) -> str:
    digest = hashlib.sha1(f"{market}|{session_id}|{ts}|{winner_type}".encode("utf-8")).hexdigest()[:10]
    return f"tradable_{digest}"


def _summarize(winners: list[dict], reject_counts: dict[str, int], candidate_evaluated: int) -> dict:
    by_type = {}
    for winner_type in TRADABLE_WINNER_TYPES:
        rows = [w for w in winners if w["winner_type"] == winner_type]
        by_type[winner_type] = {
            "count": len(rows),
            "avg_raw_return_pct": _avg(rows, "raw_return_pct"),
            "avg_effective_return_pct": _avg(rows, "effective_return_pct"),
            "avg_duration_sec": _avg(rows, "duration_seconds"),
            "tradable_with_500k": sum(1 for r in rows if r.get("tradable_with_500k")),
        }
    return {
        "tradable_winner_count": len(winners),
        "candidate_evaluated_count": candidate_evaluated,
        "winner_type_summary": by_type,
        "reject_reason_counts": reject_counts,
        "data_source": "UPBIT_WS_RECORDED",
        "real_order_enabled": False,
        "research_mode": True,
        "live_readiness": "LIVE_NOT_ALLOWED",
    }


def _avg(rows: list[dict], key: str) -> float:
    return sum(float(r.get(key, 0.0) or 0.0) for r in rows) / len(rows) if rows else 0.0
