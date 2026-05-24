from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def analyze_winner_capture_rate(winner_traces_path: str | Path, candidate_sources: str | list[str]) -> dict:
    traces = _load_traces(winner_traces_path)
    sources = _sources(candidate_sources)
    rows = []
    total = len(traces)
    for source in sources:
        counts = Counter(_classify_trace(trace, source) for trace in traces)
        captured = counts["TIMELY_CAPTURE"] + counts["EARLY_CAPTURE"]
        rows.append({
            "source": source,
            "winners": total,
            "timely_capture": counts["TIMELY_CAPTURE"],
            "early_capture": counts["EARLY_CAPTURE"],
            "late_capture": counts["LATE_CAPTURE"],
            "missed": counts["MISSED"],
            "no_data": counts["NO_DATA"],
            "capture_rate": captured / total if total else 0.0,
        })
    result = {"capture_rate_results": rows, "winner_count": total}
    out = REPLAY_STORE_DIR / "winner_mining" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "winner_capture_rate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def classify_capture(candidate_time_ms: int | None, winner_start_ms: int) -> str:
    if candidate_time_ms is None:
        return "MISSED"
    delta = winner_start_ms - candidate_time_ms
    if 0 <= delta <= 60_000:
        return "TIMELY_CAPTURE"
    if 60_000 < delta <= 300_000:
        return "EARLY_CAPTURE"
    if delta < 0:
        return "LATE_CAPTURE"
    return "MISSED"


def _classify_trace(trace: dict, source: str) -> str:
    windows = trace.get("trace_windows", {})
    if not windows:
        return "NO_DATA"
    # Research proxy: decide whether a source would have fired from pre-winner features.
    t10 = windows.get("T_MINUS_10S", {})
    t60 = windows.get("T_MINUS_60S", {})
    if source == "MICRO_ACCELERATION" and t10.get("price_change_10s_pct", 0) > 0.08 and t10.get("buy_trade_ratio_10s", 0) >= 0.52:
        return "TIMELY_CAPTURE"
    if source == "ORDERBOOK_IMBALANCE" and t10.get("orderbook_imbalance", 0) > 0.10 and t10.get("bid_ask_size_ratio", 0) >= 1.2:
        return "TIMELY_CAPTURE"
    if source == "VWAP_RECLAIM" and t60.get("vwap_distance_pct", 0) > 0 and t10.get("buy_trade_ratio_10s", 0) >= 0.5:
        return "EARLY_CAPTURE"
    if source == "EMA_PULLBACK" and t60.get("price_change_60s_pct", 0) >= 0 and t10.get("price_change_10s_pct", 0) > 0:
        return "EARLY_CAPTURE"
    return "MISSED"


def _load_traces(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.is_dir():
        path = path / "winner_traces.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("traces", data if isinstance(data, list) else [])


def _sources(value: str | list[str]) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if isinstance(value, str) else value
