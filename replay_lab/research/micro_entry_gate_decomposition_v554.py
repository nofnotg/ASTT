from __future__ import annotations

import json
from collections import Counter, defaultdict

from features.micro_entry_gate_diagnostics import diagnose_micro_entry_gates, summarize_gate_diagnostics
from replay_lab.paths import REPLAY_STORE_DIR


def diagnose_micro_entry_gates_v554(start_date=None, end_date=None, top_markets: int = 30, max_candidates: int = 50) -> dict:
    validation = _read_json("candidate_second_window_validation_v553.json") or _read_json("candidate_second_window_validation.json")
    filters = _read_json("micro_candidate_filter_validation_v553.json")
    filter_by_id = {row.get("candidate_id"): row for row in filters.get("filter_rows", [])}
    rows = []
    for row in validation.get("results", [])[:max_candidates]:
        filt = filter_by_id.get(row.get("candidate_id"), {})
        signal = _signal_from_row(row, filt)
        liquidity = _liquidity_from_filter(filt)
        diag = diagnose_micro_entry_gates(row, row, micro_signal=signal, micro_liquidity=liquidity, micro_candidate_filter=filt)
        rows.append(diag)
    summary = summarize_gate_diagnostics(rows)
    by_quality = defaultdict(Counter)
    by_market = defaultdict(Counter)
    for row in rows:
        by_quality[row.get("data_quality", "UNKNOWN")][row.get("primary_block_reason", "NONE")] += 1
        by_market[row.get("market", "UNKNOWN")][row.get("primary_block_reason", "NONE")] += 1
    result = {
        **summary,
        "period": {"start_date": str(start_date), "end_date": str(end_date)},
        "top_markets": top_markets,
        "candidate_count": validation.get("candidate_count", summary["candidate_count"]),
        "diagnosed_candidate_count": summary["candidate_count"],
        "good_partial_count": validation.get("good_partial_count", validation.get("good_window_count", 0) + validation.get("partial_window_count", 0)),
        "PASS_count": filters.get("after_PASS", 0),
        "WATCH_count": filters.get("after_WATCH", 0),
        "REJECT_count": filters.get("after_REJECT", 0),
        "ENTER_count": validation.get("enter_count", validation.get("entry_count", 0)),
        "WAIT_count": validation.get("wait_count", 0),
        "CANCEL_count": validation.get("cancel_count", 0),
        "by_quality": {key: dict(value) for key, value in by_quality.items()},
        "by_market": {key: dict(value) for key, value in by_market.items()},
        "diagnostics": rows,
    }
    out = REPLAY_STORE_DIR / "reports" / "micro_entry_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gate_diagnostics_v554.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _read_json(name: str) -> dict:
    path = REPLAY_STORE_DIR / "reports" / "upbit_real_api" / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _signal_from_row(row: dict, filter_row: dict) -> dict:
    if "micro_state_stable" in filter_row.get("reasons", []):
        return {"micro_state": "STABLE", "buy_trade_ratio_5s": 0.50}
    if row.get("entry_decision") == "ENTER":
        return {"micro_state": "ACCELERATING", "buy_trade_ratio_5s": 0.58}
    if row.get("entry_decision") == "CANCEL":
        return {"micro_state": "REVERSING", "buy_trade_ratio_5s": 0.45}
    return {"micro_state": "FADING", "buy_trade_ratio_5s": 0.50}


def _liquidity_from_filter(filter_row: dict) -> dict:
    if not filter_row:
        return {"liquidity_state": "NO_DATA", "spread_pct": None, "cost_to_target_ratio": 0.129}
    return {"liquidity_state": "NO_DATA", "spread_pct": None, "cost_to_target_ratio": filter_row.get("cost_to_target_ratio")}
