from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from winner_mining.tick_noise_filter import evaluate_tick_noise
from winner_mining.winner_effective_move import calculate_effective_move
from winner_mining.winner_liquidity_filter import estimate_liquidity_from_trace


def filter_winner_quality(winner_traces: str | Path = REPLAY_STORE_DIR / "winner_mining" / "traces", initial_cash_krw: float = 500000) -> dict:
    traces_payload = _load_json(Path(winner_traces), "winner_traces.json")
    events_payload = _load_json(REPLAY_STORE_DIR / "winner_mining" / "events", "winner_events.json")
    traces = traces_payload.get("traces", [])
    events = {row["winner_id"]: row for row in events_payload.get("events", [])}
    rows = []
    for trace in traces:
        event = events.get(trace.get("winner_id"), {})
        raw_return = float(event.get("return_pct", 0.0))
        start_price = float(event.get("start_price", 0.0))
        peak_price = float(event.get("peak_price", start_price))
        spread = _best_spread(trace)
        effective = calculate_effective_move(raw_return, spread, spread)
        tick = evaluate_tick_noise(start_price, peak_price, effective["effective_return_pct"])
        liquidity = estimate_liquidity_from_trace(trace, start_price, initial_cash_krw)
        reject_reasons = []
        if trace.get("feature_quality") not in {"GOOD", "PARTIAL"} or not event.get("source_session_id"):
            reject_reasons.append("DATA_QUALITY_POOR")
        if tick["is_tick_noise"]:
            reject_reasons.append("TICK_NOISE")
        if spread > 0.20:
            reject_reasons.append("SPREAD_TOO_WIDE")
        if not liquidity["tradable_with_500k"]:
            reject_reasons.append("INSUFFICIENT_LIQUIDITY")
        if effective["effective_return_pct"] < 0.20 or effective["reward_to_cost_ratio"] < 3.0:
            reject_reasons.append("EFFECTIVE_RETURN_TOO_LOW")
        rows.append({
            "winner_id": trace.get("winner_id"),
            "market": trace.get("market"),
            "winner_type": trace.get("winner_type"),
            **effective,
            **tick,
            **liquidity,
            "quality_filter_pass": not reject_reasons,
            "reject_reasons": reject_reasons,
            "source_session_id": event.get("source_session_id"),
            "feature_quality": trace.get("feature_quality"),
        })
    summary = _summary(rows)
    out = REPLAY_STORE_DIR / "winner_quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "quality_winners.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"summary": summary, "rows": rows}


def _summary(rows: list[dict]) -> dict:
    passed = [r for r in rows if r["quality_filter_pass"]]
    reasons = Counter(reason for row in rows for reason in row["reject_reasons"])
    by_type = defaultdict(lambda: {"raw": 0, "quality": 0, "rejected": 0, "quality_rate": 0.0})
    for row in rows:
        item = by_type[row["winner_type"]]
        item["raw"] += 1
        if row["quality_filter_pass"]:
            item["quality"] += 1
        else:
            item["rejected"] += 1
    for item in by_type.values():
        item["quality_rate"] = item["quality"] / item["raw"] if item["raw"] else 0.0
    return {
        "raw_winner_count": len(rows),
        "quality_winner_count": len(passed),
        "rejected_winner_count": len(rows) - len(passed),
        "rejection_reason_counts": dict(reasons),
        "effective_return_avg": sum(r["effective_return_pct"] for r in passed) / len(passed) if passed else 0.0,
        "reward_to_cost_avg": sum(r["reward_to_cost_ratio"] for r in passed) / len(passed) if passed else 0.0,
        "tick_noise_count": reasons.get("TICK_NOISE", 0),
        "insufficient_liquidity_count": reasons.get("INSUFFICIENT_LIQUIDITY", 0),
        "spread_too_wide_count": reasons.get("SPREAD_TOO_WIDE", 0),
        "tradable_with_500k_count": sum(1 for r in rows if r["tradable_with_500k"]),
        "winner_type_summary": dict(by_type),
        "live_readiness": "LIVE_NOT_ALLOWED",
    }


def _best_spread(trace: dict) -> float:
    values = [float(row.get("spread_pct", 999.0)) for row in trace.get("trace_windows", {}).values()]
    values = [v for v in values if v < 999.0]
    return min(values) if values else 999.0


def _load_json(path: Path, default_name: str) -> dict:
    if path.is_dir():
        path = path / default_name
    return json.loads(path.read_text(encoding="utf-8"))
