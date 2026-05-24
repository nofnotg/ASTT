from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from execution.tradable_candidate_gate_v5510 import evaluate_tradable_candidate_gate_v5510
from execution.tradable_source_paper_executor import execute_tradable_source_paper
from features.tradable_candidate_sources import TRADABLE_SOURCES, detect_all_tradable_candidates
from replay_lab.paths import REPLAY_STORE_DIR


def run_tradable_source_forward_validation_v5510(mode: str = "RECORDED_VALIDATION", initial_cash_krw: float = 500000, research_mode: bool = True, duration_minutes: int = 0) -> dict:
    snapshots = _load_tradable_snapshots()
    live_summary = _load_latest_live_summary() if mode != "RECORDED_VALIDATION" else {}
    candidates = []
    decisions = Counter()
    trades = []
    for snapshot in snapshots:
        for candidate in detect_all_tradable_candidates(snapshot, list(TRADABLE_SOURCES)):
            candidates.append(candidate)
            gate = evaluate_tradable_candidate_gate_v5510(candidate)
            decisions[gate["decision"]] += 1
            trade = execute_tradable_source_paper(candidate, gate["decision"], initial_cash_krw)
            if trade["paper_trade_created"]:
                trades.append(trade)
    by_source = Counter(c["candidate_source"] for c in candidates)
    grade_rows = _grade_rows(by_source, decisions.get("ENTER", 0))
    session_id = datetime.utcnow().strftime("tradable_forward_%Y%m%d_%H%M%S")
    summary = {
        "session_id": session_id,
        "mode": mode,
        "data_source": "UPBIT_WS_RECORDED" if mode == "RECORDED_VALIDATION" else "UPBIT_WS_LIVE",
        "duration_minutes": duration_minutes,
        "trade_event_count": int(live_summary.get("trade_event_count", 0) or 0),
        "orderbook_event_count": int(live_summary.get("orderbook_event_count", 0) or 0),
        "ticker_event_count": int(live_summary.get("ticker_event_count", 0) or 0),
        "live_session_quality": live_summary.get("quality", "NO_DATA") if mode != "RECORDED_VALIDATION" else "N/A",
        "candidate_count": len(candidates),
        "candidate_by_source": dict(by_source),
        "gate_pass_count": decisions.get("ENTER", 0),
        "ENTER": decisions.get("ENTER", 0),
        "WAIT": decisions.get("WAIT", 0),
        "CANCEL": decisions.get("CANCEL", 0),
        "paper_trade_count": len(trades),
        "pnl_evaluable": bool(trades),
        "total_pnl_krw": sum(t.get("total_pnl_krw", 0.0) for t in trades) if trades else None,
        "total_return_pct": 0.0 if trades else None,
        "max_drawdown_pct": 0.0 if trades else None,
        "win_rate": 0.0 if trades else None,
        "profit_factor": 0.0 if trades else None,
        "expectancy_pct": 0.0 if trades else None,
        "avg_hold_seconds": 0.0 if trades else None,
        "full_seed_grade_rows": grade_rows,
        "real_order_enabled": False,
        "research_mode": research_mode,
        "live_readiness": "LIVE_NOT_ALLOWED",
    }
    out = REPLAY_STORE_DIR / "tradable_forward" / session_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = REPLAY_STORE_DIR / "tradable_forward" / "latest_tradable_forward_summary.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _load_latest_live_summary() -> dict:
    path = REPLAY_STORE_DIR / "live_v5510" / "latest_live_session_summary.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _load_tradable_snapshots() -> list[dict]:
    path = REPLAY_STORE_DIR / "tradable_trace" / "tradable_traces.json"
    if not path.exists():
        return []
    traces = json.loads(path.read_text(encoding="utf-8")).get("traces", [])
    snapshots = []
    for trace in traces:
        for row in trace.get("trace_windows", {}).values():
            snapshots.append(row)
    return snapshots


def _grade_rows(by_source: Counter, enter_count: int) -> list[dict]:
    rows = []
    for source in TRADABLE_SOURCES:
        count = by_source.get(source, 0)
        rows.append({
            "source": source,
            "candidate": count,
            "grade_c": 0 if count else 1,
            "grade_b": count,
            "grade_a": 0,
            "grade_s": 0,
            "allocation_candidate": count,
            "ENTER": enter_count if count else 0,
        })
    return rows
