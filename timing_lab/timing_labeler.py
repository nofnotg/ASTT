from __future__ import annotations

from pathlib import Path
from typing import Any

from timing_lab.entry_window_analyzer import analyze_clip_entry_windows
from timing_lab.event_clip_store import read_jsonl


def label_clip(clip_dir: str | Path, initial_cash_krw: float = 500000) -> dict[str, Any]:
    clip_dir = Path(clip_dir)
    meta = _read_meta(clip_dir)
    analysis = analyze_clip_entry_windows(clip_dir, initial_cash_krw)
    best = analysis.get("best_window") or {}
    trades = read_jsonl(clip_dir / "trades.jsonl")
    event_time = int(meta.get("event_time_ms", 0))
    label = "ENTRY_WINDOW" if best else _fallback_label(meta, trades, event_time)
    return {
        "clip_id": meta.get("clip_id", clip_dir.name),
        "event_id": meta.get("event_id", ""),
        "market": meta.get("market", ""),
        "label": label,
        "entry_window_start_ms": int(best.get("start_ms", 0)),
        "entry_window_end_ms": int(best.get("end_ms", 0)),
        "window_duration_seconds": int(best.get("duration_seconds", 0)),
        "max_effective_return_pct": float(best.get("effective_return_pct", 0.0)),
        "max_mfe_pct": _mfe_pct(trades, event_time),
        "max_mae_pct": _mae_pct(trades, event_time),
        "tradable_with_500k": bool(best.get("tradable_with_500k", False)),
        "reason": analysis.get("no_entry_reason", []),
        "quality": meta.get("quality", "POOR"),
    }


def label_event_clips(clips_dir: str | Path, output_dir: str | Path = "replay_store/timing_labels") -> dict[str, Any]:
    root = Path(clips_dir)
    labels = []
    for path in root.glob("*/*/clip_meta.json"):
        meta = _read_meta(path.parent)
        if str(meta.get("market", "")).endswith("TEST"):
            continue
        labels.append(label_clip(path.parent))
    counts: dict[str, int] = {}
    for row in labels:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"label_count": len(labels), "label_counts": counts, "labels": labels}
    (out / "latest_timing_labels.json").write_text(__import__("json").dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _fallback_label(meta: dict[str, Any], trades: list[dict[str, Any]], event_time: int) -> str:
    if meta.get("status") != "CLOSED":
        return "NO_TRADE"
    if meta.get("quality") == "POOR":
        return "NO_TRADE"
    mfe = _mfe_pct(trades, event_time)
    mae = _mae_pct(trades, event_time)
    if mfe <= 0.05:
        return "FAKE_SIGNAL"
    if mae < -0.2:
        return "TOO_EARLY"
    if mfe < 0.1:
        return "TOO_LATE"
    return "SPREAD_TRAP"


def _mfe_pct(trades: list[dict[str, Any]], event_time: int) -> float:
    post = [row for row in trades if int(row.get("timestamp_ms", 0)) >= event_time and float(row.get("trade_price") or 0) > 0]
    if not post:
        return 0.0
    entry = float(post[0]["trade_price"])
    return (max(float(row["trade_price"]) for row in post) - entry) / entry * 100 if entry else 0.0


def _mae_pct(trades: list[dict[str, Any]], event_time: int) -> float:
    post = [row for row in trades if int(row.get("timestamp_ms", 0)) >= event_time and float(row.get("trade_price") or 0) > 0]
    if not post:
        return 0.0
    entry = float(post[0]["trade_price"])
    return (min(float(row["trade_price"]) for row in post) - entry) / entry * 100 if entry else 0.0


def _read_meta(clip_dir: Path) -> dict[str, Any]:
    path = clip_dir / "clip_meta.json"
    return __import__("json").loads(path.read_text(encoding="utf-8")) if path.exists() else {}
