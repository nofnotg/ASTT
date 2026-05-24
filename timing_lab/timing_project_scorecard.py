from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from timing_lab.project_kill_criteria import decide_project


def build_project_scorecard() -> dict[str, Any]:
    timing = _read("docs/reports/latest_timing_lab_summary.json")
    entry = _read("docs/reports/latest_entry_timing_summary.json")
    llm = _read("docs/reports/latest_llm_completion_repair_summary.json")
    fake = _read("replay_store/fake_signal/fake_signal_decomposition.json")
    categories = {
        "Data Collection Stability": 15 if timing.get("clip_quality_counts", {}).get("GOOD", 0) > 0 else 0,
        "Event Quality": 5 if fake.get("fake_signal_count", 0) else 0,
        "Entry Window Discovery": 20 if entry.get("entry_window_count", 0) > 0 else 0,
        "Confirmation Quality": 20 if entry.get("state_transition_counts", {}).get("TRIGGERED -> CONFIRMED", 0) > 0 else 0,
        "Paper Execution Evidence": 15 if entry.get("paper_execution", {}).get("paper_enter_count", 0) > 0 else 0,
        "LLM Review Utility": 10 if llm.get("completion_tokens", 0) > 0 and not llm.get("fallback_used", True) else 2,
        "Operational Simplicity": 4,
    }
    total = sum(categories.values())
    decision = decide_project(total, entry.get("entry_window_count", 0), entry.get("state_transition_counts", {}).get("TRIGGERED -> CONFIRMED", 0), entry.get("paper_execution", {}).get("paper_enter_count", 0))
    summary = {"category_scores": categories, "total_score": total, **decision}
    _write(Path("replay_store/project_scorecard/project_scorecard_v5r2.json"), summary)
    return summary


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
