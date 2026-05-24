from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from execution.timing_based_entry_executor import execute_timing_entry
from execution.timing_based_position_manager import close_timing_position
from timing_lab.entry_window_analyzer import analyze_entry_windows
from timing_lab.timing_labeler import label_event_clips
from timing_lab.timing_state_machine import validate_state_machine_for_clips


def run_timing_based_paper_v5r1(clips_dir: str | Path, initial_cash_krw: float = 500000, research_mode: bool = True) -> dict[str, Any]:
    labels_payload = label_event_clips(clips_dir)
    labels = labels_payload.get("labels", [])
    windows_payload = analyze_entry_windows(clips_dir, initial_cash_krw)
    state_payload = validate_state_machine_for_clips(clips_dir, labels)
    window_by_clip = {analysis["clip_id"]: analysis.get("best_window", {}) for analysis in windows_payload.get("analyses", [])}
    executions = []
    for state in state_payload.get("states", []):
        if state.get("state") != "ENTER":
            continue
        entry = execute_timing_entry({"state": "CONFIRMED"}, window_by_clip.get(_clip_id_from_event(state.get("event_id", "")), {}), initial_cash_krw)
        close = close_timing_position(entry, entry.get("entry_price"))
        executions.append({**entry, **close, "event_id": state.get("event_id"), "clip_id": _clip_id_from_event(state.get("event_id", ""))})
    summary = {
        "initial_cash_krw": initial_cash_krw,
        "research_mode": research_mode,
        "real_order_enabled": False,
        "paper_enter_count": sum(1 for row in executions if row.get("paper_entered")),
        "trade_count": sum(1 for row in executions if row.get("paper_entered")),
        "pnl_evaluable": any(row.get("pnl_evaluable") for row in executions),
        "total_pnl_krw": sum(float(row.get("realistic_1_pnl_krw", 0.0)) for row in executions),
        "total_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "realistic_1_status": "EVALUABLE" if executions else "N/A",
        "executions": executions,
    }
    out = Path("replay_store/timing_state_replay")
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_timing_based_paper_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _clip_id_from_event(event_id: str) -> str:
    return f"{event_id}_clip"
