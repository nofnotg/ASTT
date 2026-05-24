from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from timing_lab.event_clip_store import read_jsonl


FAILURE_TYPES = ["PRICE_NO_MOVE", "MOVE_TOO_SMALL", "MOVE_REVERSED", "BUY_RATIO_DROPPED", "SPREAD_WIDENED", "DEPTH_EVAPORATED", "BTC_REVERSED", "TIMEOUT", "UNKNOWN"]


def analyze_follow_through_failures(clips_dir: str | Path, state_path: str | Path = "replay_store/timing_state_replay/latest_state_machine_summary.json") -> dict[str, Any]:
    states = _read(state_path).get("states", [])
    rows = []
    for state in states:
        if "FOLLOW_THROUGH_FAIL" not in state.get("abort_reasons", []):
            continue
        clip_id = f"{state['event_id']}_clip"
        meta, trades, orderbooks = _clip_data(Path(clips_dir), clip_id)
        rows.append(_analyze_state(state, meta, trades, orderbooks))
    counts = Counter(row["failure_type"] for row in rows)
    total = max(1, len(rows))
    summary = {
        "follow_through_fail_count": len(rows),
        "classified_count": sum(v for k, v in counts.items() if k != "UNKNOWN"),
        "unknown_count": counts.get("UNKNOWN", 0),
        "unknown_rate": counts.get("UNKNOWN", 0) / total,
        "failure_counts": dict(counts),
        "failure_table": [
            {
                "failure_type": kind,
                "count": counts.get(kind, 0),
                "pct": counts.get(kind, 0) / total * 100,
                "suggested_calibration": _suggestion(kind),
            }
            for kind in FAILURE_TYPES
        ],
        "rows": rows,
    }
    _write(Path("replay_store/follow_through_failures/follow_through_failures.json"), summary)
    return summary


def _analyze_state(state: dict[str, Any], meta: dict[str, Any], trades: list[dict[str, Any]], orderbooks: list[dict[str, Any]]) -> dict[str, Any]:
    event_time = int(meta.get("event_time_ms") or state.get("state_entered_at_ms") or 0)
    post = [row for row in trades if int(row.get("timestamp_ms", 0)) >= event_time]
    prices = [float(row.get("trade_price") or 0) for row in post if float(row.get("trade_price") or 0) > 0]
    change = 0.0
    if len(prices) >= 2 and prices[0]:
        change = (max(prices) - prices[0]) / prices[0] * 100
    buy_ratio = _buy_ratio(post)
    failure = "PRICE_NO_MOVE"
    if not post:
        failure = "TIMEOUT"
    elif change <= 0.01:
        failure = "PRICE_NO_MOVE"
    elif change <= 0.08:
        failure = "MOVE_TOO_SMALL"
    elif prices and prices[-1] < prices[0]:
        failure = "MOVE_REVERSED"
    elif buy_ratio < 0.5:
        failure = "BUY_RATIO_DROPPED"
    return {
        "event_id": state.get("event_id", ""),
        "market": state.get("market", ""),
        "failure_type": failure,
        "triggered_at_ms": event_time,
        "confirmation_window_seconds": 30,
        "post_trigger_price_change_pct": change,
        "post_trigger_effective_return_pct": change - 0.15,
        "buy_ratio_change": buy_ratio - float(state.get("evidence", {}).get("buy_trade_ratio", 0.0)),
        "spread_change_pct": 0.0,
        "depth_change_krw": 0.0,
        "evidence": {"post_trade_count": len(post), "post_orderbook_count": len(orderbooks), "buy_ratio": buy_ratio},
        "suggested_calibration": _suggestion(failure),
    }


def _buy_ratio(trades: list[dict[str, Any]]) -> float:
    return sum(1 for row in trades if row.get("ask_bid") == "BID") / len(trades) if trades else 0.0


def _suggestion(kind: str) -> dict[str, Any]:
    return {
        "PRICE_NO_MOVE": {"tighten_trigger": True, "min_price_follow_pct": 0.05},
        "MOVE_TOO_SMALL": {"raise_reward_to_cost": True},
        "MOVE_REVERSED": {"add_confirmation_delay": True},
        "BUY_RATIO_DROPPED": {"min_buy_ratio_hold": 0.55},
        "SPREAD_WIDENED": {"max_spread_widening_pct": 0.03},
        "DEPTH_EVAPORATED": {"min_depth_ratio_hold": 1.0},
        "BTC_REVERSED": {"btc_abort_rule": True},
        "TIMEOUT": {"confirmation_window_seconds": 60},
    }.get(kind, {"review_required": True})


def _clip_data(root: Path, clip_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    for meta_path in root.glob(f"*\\{clip_id}\\clip_meta.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        return meta, read_jsonl(meta_path.parent / "trades.jsonl"), read_jsonl(meta_path.parent / "orderbooks.jsonl")
    return {}, [], []


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
