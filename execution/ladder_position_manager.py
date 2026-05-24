from __future__ import annotations


def validate_ladder_position_plan(entry_ladder: dict, exit_ladder: dict) -> dict:
    entry_pct = round(sum(step.get("pct", 0.0) for step in entry_ladder.get("ladder_plan", [])), 8)
    exit_pct = round(sum(step.get("pct", 0.0) for step in exit_ladder.get("exit_plan", [])), 8)
    return {
        "valid": entry_pct == 1.0 and exit_pct == 1.0,
        "entry_pct_total": entry_pct,
        "exit_pct_total": exit_pct,
        "warnings": [] if entry_pct == 1.0 and exit_pct == 1.0 else ["LADDER_PCT_TOTAL_INVALID"],
    }
