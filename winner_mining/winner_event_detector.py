from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from winner_mining.winner_event_schema import WINNER_RULES, build_winner_event


def detect_winner_events_from_sessions(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions", winner_types: str | list[str] | None = None) -> dict:
    selected = _winner_types(winner_types)
    raw_roots = _discover_raw_roots(Path(sessions_dir))
    events: list[dict] = []
    source_session_ids: list[str] = []
    for root in raw_roots:
        source_session_ids.append(root.name)
        for path in (root / "trades").glob("*.jsonl"):
            trades = _read_jsonl(path, limit=200000)
            seconds = build_second_series(trades)
            for event in detect_winner_events(seconds, selected):
                event["source_session_id"] = root.name
                events.append(event)
    summary = _summary(events, source_session_ids)
    out = REPLAY_STORE_DIR / "winner_mining" / "events"
    out.mkdir(parents=True, exist_ok=True)
    (out / "winner_events.json").write_text(json.dumps({"summary": summary, "events": events}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"summary": summary, "events": events}


def detect_winner_events(seconds: list[dict], winner_types: list[str] | None = None) -> list[dict]:
    if len(seconds) < 2:
        return []
    selected = winner_types or list(WINNER_RULES)
    events: list[dict] = []
    market = seconds[0].get("market", "")
    for winner_type in selected:
        rule = WINNER_RULES[winner_type]
        last_peak_ms = -1
        for i, start in enumerate(seconds):
            start_ms = int(start["timestamp_ms"])
            if start_ms <= last_peak_ms:
                continue
            candidates = [
                row for row in seconds[i + 1 :]
                if rule["min_seconds"] * 1000 <= int(row["timestamp_ms"]) - start_ms <= rule["max_seconds"] * 1000
            ]
            if not candidates:
                continue
            peak = max(candidates, key=lambda row: float(row.get("high", row.get("price", 0.0))))
            event = build_winner_event(market, winner_type, start, peak, quality="GOOD" if len(candidates) >= max(1, rule["min_seconds"] // 2) else "PARTIAL")
            if event["return_pct"] >= rule["return_pct"]:
                events.append(event)
                last_peak_ms = event["peak_time_ms"]
    return events


def build_second_series(trades: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int], dict] = {}
    for event in sorted(trades, key=lambda x: int(x.get("timestamp_ms", 0))):
        market = event.get("market", "")
        ts = int(event.get("timestamp_ms", 0))
        sec_ms = ts - (ts % 1000)
        price = float(event.get("trade_price", 0.0))
        key = (market, sec_ms)
        row = grouped.setdefault(key, {"market": market, "timestamp_ms": sec_ms, "open": price, "high": price, "low": price, "price": price, "volume": 0.0, "buy_volume": 0.0, "sell_volume": 0.0, "trade_count": 0})
        row["high"] = max(row["high"], price)
        row["low"] = min(row["low"], price)
        row["price"] = price
        volume = float(event.get("trade_volume", 0.0))
        row["volume"] += volume
        row["trade_count"] += 1
        if str(event.get("ask_bid", "")).upper() == "BID":
            row["buy_volume"] += volume
        else:
            row["sell_volume"] += volume
    return [grouped[key] for key in sorted(grouped)]


def _discover_raw_roots(sessions_dir: Path) -> list[Path]:
    raw_base = REPLAY_STORE_DIR / "raw" / "upbit_ws"
    session_ids: set[str] = set()
    for path in sessions_dir.rglob("session_summary.json"):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if summary.get("data_source") == "UPBIT_WS" or summary.get("source_session", {}).get("data_source") == "UPBIT_WS":
            session_ids.add(summary.get("session_id") or summary.get("source_session", {}).get("session_id", ""))
            if summary.get("source_session", {}).get("session_id"):
                session_ids.add(summary["source_session"]["session_id"])
    roots = [path for path in raw_base.glob("*/*") if path.is_dir() and (not session_ids or path.name in session_ids)]
    return roots


def _read_jsonl(path: Path, limit: int) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i >= limit:
                break
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _winner_types(value: str | list[str] | None) -> list[str]:
    if not value:
        return list(WINNER_RULES)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def _summary(events: list[dict], source_session_ids: list[str]) -> dict:
    by_type = defaultdict(list)
    for event in events:
        by_type[event["winner_type"]].append(event)
    rows = {}
    for winner_type in WINNER_RULES:
        items = by_type[winner_type]
        rows[winner_type] = {
            "count": len(items),
            "avg_return_pct": sum(e["return_pct"] for e in items) / len(items) if items else 0.0,
            "avg_duration_sec": sum(e["duration_seconds"] for e in items) / len(items) if items else 0.0,
            "quality": "GOOD" if items else "NO_DATA",
        }
    return {"winner_event_count": len(events), "winner_type_summary": rows, "source_session_ids": sorted(set(source_session_ids)), "data_source": "UPBIT_WS", "live_readiness": "LIVE_NOT_ALLOWED"}
