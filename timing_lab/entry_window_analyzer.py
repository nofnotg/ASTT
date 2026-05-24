from __future__ import annotations

from pathlib import Path
from typing import Any

from timing_lab.event_clip_store import read_jsonl


def analyze_clip_entry_windows(clip_dir: str | Path, initial_cash_krw: float = 500000) -> dict[str, Any]:
    clip_dir = Path(clip_dir)
    meta = _read_meta(clip_dir)
    trades = read_jsonl(clip_dir / "trades.jsonl")
    orderbooks = read_jsonl(clip_dir / "orderbooks.jsonl")
    event_time = int(meta.get("event_time_ms", 0))
    post_trades = [row for row in trades if int(row.get("timestamp_ms", 0)) >= event_time and float(row.get("trade_price") or 0) > 0]
    windows: list[dict[str, Any]] = []
    for idx, trade in enumerate(post_trades):
        entry_time = int(trade["timestamp_ms"])
        entry_price = float(trade["trade_price"])
        future = [row for row in post_trades[idx:] if int(row["timestamp_ms"]) <= entry_time + 300_000]
        if not future:
            continue
        max_exit_price = max(float(row["trade_price"]) for row in future)
        raw_return = (max_exit_price - entry_price) / entry_price * 100 if entry_price else 0.0
        spread_pct = _nearest_spread_pct(orderbooks, entry_time)
        depth_krw = _nearest_depth_krw(orderbooks, entry_time)
        total_cost = max(0.05, spread_pct * 2 + 0.05)
        effective = raw_return - total_cost
        reward_to_cost = raw_return / total_cost if total_cost > 0 else 999.0
        tick_noise = raw_return < 0.08
        tradable = effective > 0 and reward_to_cost >= 3 and depth_krw >= initial_cash_krw and not tick_noise
        if tradable:
            windows.append(
                {
                    "start_ms": entry_time,
                    "end_ms": min(entry_time + 30_000, int(future[-1]["timestamp_ms"])),
                    "duration_seconds": max(1, min(30, int((int(future[-1]["timestamp_ms"]) - entry_time) / 1000))),
                    "entry_price": entry_price,
                    "max_exit_price": max_exit_price,
                    "effective_return_pct": effective,
                    "reward_to_cost_ratio": reward_to_cost,
                    "tradable_with_500k": True,
                    "window_quality": meta.get("quality", "POOR"),
                }
            )
    best = max(windows, key=lambda item: item["effective_return_pct"], default={})
    reasons = []
    if not post_trades:
        reasons.append("NO_POST_EVENT_TRADES")
    if not windows:
        reasons.append("NO_TRADABLE_ENTRY_WINDOW")
    return {"clip_id": meta.get("clip_id", clip_dir.name), "entry_windows": windows, "best_window": best, "no_entry_reason": reasons}


def analyze_entry_windows(clips_dir: str | Path, initial_cash_krw: float = 500000) -> dict[str, Any]:
    root = Path(clips_dir)
    analyses = []
    for path in root.glob("*/*/clip_meta.json"):
        meta = _read_meta(path.parent)
        if str(meta.get("market", "")).endswith("TEST"):
            continue
        analyses.append(analyze_clip_entry_windows(path.parent, initial_cash_krw))
    entry_windows = [window for row in analyses for window in row["entry_windows"]]
    best = max(entry_windows, key=lambda item: item["effective_return_pct"], default={})
    summary = {
        "entry_window_count": len(entry_windows),
        "avg_window_duration_seconds": sum(w["duration_seconds"] for w in entry_windows) / len(entry_windows) if entry_windows else 0.0,
        "best_effective_return_pct": best.get("effective_return_pct", 0.0),
        "tradable_with_500k_count": sum(1 for w in entry_windows if w.get("tradable_with_500k")),
        "analyses": analyses,
    }
    return summary


def _read_meta(clip_dir: Path) -> dict[str, Any]:
    path = clip_dir / "clip_meta.json"
    return __import__("json").loads(path.read_text(encoding="utf-8")) if path.exists() else {"clip_id": clip_dir.name}


def _nearest_spread_pct(orderbooks: list[dict[str, Any]], ts: int) -> float:
    if not orderbooks:
        return 0.2
    row = min(orderbooks, key=lambda item: abs(int(item.get("timestamp_ms", 0)) - ts))
    units = row.get("units") or row.get("raw", {}).get("orderbook_units", [])
    if not units:
        return 0.2
    ask = float(units[0].get("ask_price") or 0)
    bid = float(units[0].get("bid_price") or 0)
    mid = (ask + bid) / 2 if ask and bid else 0
    return (ask - bid) / mid * 100 if mid else 0.2


def _nearest_depth_krw(orderbooks: list[dict[str, Any]], ts: int) -> float:
    if not orderbooks:
        return 0.0
    row = min(orderbooks, key=lambda item: abs(int(item.get("timestamp_ms", 0)) - ts))
    units = row.get("units") or row.get("raw", {}).get("orderbook_units", [])
    return sum(float(unit.get("ask_price") or 0) * float(unit.get("ask_size") or 0) for unit in units[:3])
