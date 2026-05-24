from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from winner_mining.winner_feature_snapshot import compute_winner_feature_snapshot


def extract_winner_traces(winner_events_path: str | Path = REPLAY_STORE_DIR / "winner_mining" / "events", trace_windows: str | list[int] = "10,30,60,180,300") -> dict:
    events = _load_events(winner_events_path)
    windows = _windows(trace_windows)
    raw_cache: dict[tuple[str, str], tuple[list[dict], list[dict]]] = {}
    traces = []
    for event in events:
        root = _find_raw_root(event.get("market", ""), event.get("source_session_id"))
        if not root:
            traces.append({"winner_id": event["winner_id"], "market": event["market"], "winner_type": event["winner_type"], "trace_windows": {}, "feature_quality": "POOR", "warnings": ["raw_session_missing"]})
            continue
        key = (str(root), event["market"])
        if key not in raw_cache:
            raw_cache[key] = (_read_jsonl(root / "trades" / f"{event['market']}.jsonl", 200000), _read_jsonl(root / "orderbooks" / f"{event['market']}.jsonl", 200000))
        trades, orderbooks = raw_cache[key]
        trace_windows_map = {}
        for seconds in windows:
            as_of = int(event["start_time_ms"]) - seconds * 1000
            trace_windows_map[f"T_MINUS_{seconds}S"] = _feature_set(trades, orderbooks, as_of)
        quality = _feature_quality(trace_windows_map)
        traces.append({"winner_id": event["winner_id"], "market": event["market"], "winner_type": event["winner_type"], "trace_windows": trace_windows_map, "feature_quality": quality, "warnings": [] if quality != "POOR" else ["thin_pre_winner_trace"]})
    summary = {"trace_count": len(traces), "good_partial_trace_count": sum(1 for t in traces if t["feature_quality"] in {"GOOD", "PARTIAL"}), "trace_windows": windows}
    out = REPLAY_STORE_DIR / "winner_mining" / "traces"
    out.mkdir(parents=True, exist_ok=True)
    (out / "winner_traces.json").write_text(json.dumps({"summary": summary, "traces": traces}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"summary": summary, "traces": traces}


def _feature_set(trades: list[dict], orderbooks: list[dict], as_of_ms: int) -> dict:
    base = compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 60)
    return {
        "price_change_3s_pct": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 3)["price_change_pct"],
        "price_change_5s_pct": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 5)["price_change_pct"],
        "price_change_10s_pct": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["price_change_pct"],
        "price_change_30s_pct": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 30)["price_change_pct"],
        "price_change_60s_pct": base["price_change_pct"],
        "range_position_pct": base["range_position_pct"],
        "previous_high_distance_pct": base["previous_high_distance_pct"],
        "breakout_distance_pct": base["breakout_distance_pct"],
        "volume_10s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["volume"],
        "volume_30s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 30)["volume"],
        "volume_60s": base["volume"],
        "volume_burst_ratio_10s_vs_60s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["volume"] / (base["volume"] / 6) if base["volume"] else 0.0,
        "trade_count_10s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["trade_count"],
        "trade_count_acceleration": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["trade_count"] / max(1, base["trade_count"] / 6),
        "buy_trade_ratio_5s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 5)["buy_trade_ratio"],
        "buy_trade_ratio_10s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["buy_trade_ratio"],
        "buy_trade_ratio_30s": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 30)["buy_trade_ratio"],
        "aggressive_buy_ratio": compute_winner_feature_snapshot(trades, orderbooks, as_of_ms, 10)["buy_trade_ratio"],
        "spread_pct": base["spread_pct"],
        "bid_ask_size_ratio": base["bid_ask_size_ratio"],
        "orderbook_imbalance": base["orderbook_imbalance"],
        "vwap_distance_pct": base["vwap_distance_pct"],
        "ema20_distance_pct": base["ema20_distance_pct"],
        "ema50_distance_pct": base["ema50_distance_pct"],
        "btc_micro_state": "UNKNOWN",
        "btc_1m_change_pct": 0.0,
        "market_breadth_up_ratio": 0.0,
        "krw_market_volume_rank": 0,
    }


def _load_events(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.is_dir():
        path = path / "winner_events.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("events", data if isinstance(data, list) else [])


def _find_raw_root(market: str, source_session_id: str | None = None) -> Path | None:
    if source_session_id:
        for root in (REPLAY_STORE_DIR / "raw" / "upbit_ws").glob("*/*"):
            if root.name != source_session_id:
                continue
            if (root / "trades" / f"{market}.jsonl").exists():
                return root
    for root in sorted((REPLAY_STORE_DIR / "raw" / "upbit_ws").glob("*/*"), reverse=True):
        if (root / "trades" / f"{market}.jsonl").exists():
            return root
    return None


def _feature_quality(trace_windows_map: dict[str, dict]) -> str:
    if not trace_windows_map:
        return "POOR"
    active = 0
    for row in trace_windows_map.values():
        has_trade = float(row.get("volume_60s", 0.0)) > 0 or int(row.get("trade_count_10s", 0)) > 0
        has_orderbook = float(row.get("spread_pct", 999.0)) < 10.0 and float(row.get("bid_ask_size_ratio", 0.0)) > 0
        if has_trade or has_orderbook:
            active += 1
    coverage = active / max(1, len(trace_windows_map))
    if coverage >= 0.6:
        return "GOOD"
    if coverage >= 0.2:
        return "PARTIAL"
    return "POOR"


def _read_jsonl(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i >= limit:
                break
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _windows(value: str | list[int]) -> list[int]:
    if isinstance(value, str):
        return [int(item.strip()) for item in value.split(",") if item.strip()]
    return [int(v) for v in value]
