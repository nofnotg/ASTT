from __future__ import annotations

from capital.entry_ladder import build_entry_ladder
from capital.exit_ladder import build_exit_ladder
from execution.ladder_position_manager import validate_ladder_position_plan


def validate_ladder_entry_exit_v557(sessions_dir: str = "replay_store/sessions/realistic_paper_v555") -> dict:
    entry = build_entry_ladder(500000)
    exit_plan = build_exit_ladder()
    validation = validate_ladder_position_plan(entry, exit_plan)
    return {"sessions_dir": sessions_dir, "entry_ladder": entry, "exit_ladder": exit_plan, "ladder_validation_result": validation}
