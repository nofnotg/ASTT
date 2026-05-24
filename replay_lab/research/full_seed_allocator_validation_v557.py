from __future__ import annotations

from execution.full_seed_paper_runner import run_full_seed_paper_session_v557
from replay_lab.research.sizing_mode_comparison_v557 import compare_sizing_modes_v557
from replay_lab.research.ladder_entry_exit_validation_v557 import validate_ladder_entry_exit_v557


def validate_full_seed_allocator_v557(initial_cash_krw: float = 500000) -> dict:
    session = run_full_seed_paper_session_v557(duration_minutes=0, initial_cash_krw=initial_cash_krw)
    sizing = compare_sizing_modes_v557(initial_cash_krw=initial_cash_krw)
    ladder = validate_ladder_entry_exit_v557()
    return {"session": session, "sizing": sizing, "ladder": ladder}
