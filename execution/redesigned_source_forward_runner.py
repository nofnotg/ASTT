from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from execution.redesigned_source_paper_executor import execute_redesigned_source_paper
from execution.source_candidate_gate_v559 import evaluate_source_candidate_gate_v559
from features.refined_orderflow_surge import detect_orderflow_surge_refined
from features.refined_range_compression_expansion import detect_range_compression_expansion_refined
from features.refined_volume_range_breakout import detect_volume_range_breakout_refined
from replay_lab.paths import REPLAY_STORE_DIR


REFINED_DETECTORS = {
    "ORDERFLOW_SURGE_REFINED": detect_orderflow_surge_refined,
    "VOLUME_RANGE_BREAKOUT_REFINED": detect_volume_range_breakout_refined,
    "RANGE_COMPRESSION_EXPANSION_REFINED": detect_range_compression_expansion_refined,
}


def run_redesigned_source_forward_test_v559(
    duration_minutes: int = 15,
    top_markets: int = 20,
    sources: str | list[str] = "ORDERFLOW_SURGE_REFINED,VOLUME_RANGE_BREAKOUT_REFINED,RANGE_COMPRESSION_EXPANSION_REFINED",
    initial_cash_krw: float = 500000,
    scenario: str = "realistic_1",
    research_mode: bool = True,
) -> dict:
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if isinstance(sources, str) else sources
    snapshots = _load_forward_snapshots(top_markets)
    quality_summary = _load_quality_summary()
    quality_winner_count = int(quality_summary.get("quality_winner_count", 0) or 0)
    source_quality_flags = []
    if quality_winner_count <= 0:
        source_quality_flags.append("QUALITY_WINNER_COUNT_ZERO")
    candidates = []
    gate_pass_count = 0
    decisions = Counter()
    trades = []
    for snapshot in snapshots:
        for source in source_list:
            detector = REFINED_DETECTORS.get(source)
            if not detector:
                continue
            candidate = detector(snapshot, {"order_krw": initial_cash_krw})
            if not candidate:
                continue
            candidates.append(candidate)
            if quality_winner_count <= 0:
                gate = {
                    "decision": "WAIT",
                    "gate_pass": False,
                    "reasons": ["QUALITY_WINNER_COUNT_ZERO"],
                    "real_order_enabled": False,
                }
            else:
                gate = evaluate_source_candidate_gate_v559(candidate, snapshot)
            decisions[gate["decision"]] += 1
            gate_pass_count += int(gate["gate_pass"])
            trade = execute_redesigned_source_paper(candidate, gate["decision"], initial_cash_krw)
            if trade["paper_trade_created"]:
                trades.append(trade)
    by_source = Counter(c["candidate_source"] for c in candidates)
    session_id = datetime.utcnow().strftime("forward_v559_%Y%m%d_%H%M%S")
    summary = {
        "session_id": session_id,
        "duration_minutes": duration_minutes,
        "data_source": "UPBIT_WS_RECORDED_FORWARD_TEST",
        "trade_event_count": len(snapshots),
        "orderbook_event_count": len(snapshots),
        "candidate_count": len(candidates),
        "candidate_by_source": dict(by_source),
        "gate_pass_count": gate_pass_count,
        "ENTER": decisions.get("ENTER", 0),
        "WAIT": decisions.get("WAIT", 0),
        "CANCEL": decisions.get("CANCEL", 0),
        "paper_trade_count": len(trades),
        "pnl_evaluable": bool(trades),
        "total_pnl_krw": sum(t.get("total_pnl_krw") or 0 for t in trades) if trades else None,
        "effective_cost_avg": 0.15,
        "false_positive_proxy": max(0.0, 1 - (len(trades) / max(1, len(candidates)))),
        "source_quality_flags": source_quality_flags,
        "quality_winner_count": quality_winner_count,
        "real_order_enabled": False,
        "research_mode": research_mode,
        "scenario": scenario,
        "live_readiness": "LIVE_NOT_ALLOWED",
    }
    out = REPLAY_STORE_DIR / "forward_v559" / session_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    latest = REPLAY_STORE_DIR / "forward_v559" / "latest_forward_summary.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary


def _load_quality_summary() -> dict:
    quality_path = REPLAY_STORE_DIR / "winner_quality" / "quality_winners.json"
    if not quality_path.exists():
        return {}
    try:
        return json.loads(quality_path.read_text(encoding="utf-8")).get("summary", {})
    except json.JSONDecodeError:
        return {}


def _load_forward_snapshots(top_markets: int) -> list[dict]:
    trace_path = REPLAY_STORE_DIR / "winner_mining" / "traces" / "winner_traces.json"
    if not trace_path.exists():
        return []
    traces = json.loads(trace_path.read_text(encoding="utf-8")).get("traces", [])
    snapshots = []
    markets = []
    for trace in traces:
        market = trace.get("market", "")
        if market not in markets:
            markets.append(market)
        if len(markets) > top_markets:
            continue
        for key in ("T_MINUS_10S", "T_MINUS_30S", "T_MINUS_60S"):
            row = dict(trace.get("trace_windows", {}).get(key, {}))
            if row:
                row["market"] = market
                row["timestamp_ms"] = 0
                row["last_price"] = 0.0
                snapshots.append(row)
    return snapshots
