from __future__ import annotations

from execution.forward_paper_micro_runner import run_forward_paper_micro_session


def run_live_micro_session(**kwargs) -> dict:
    return run_forward_paper_micro_session(**kwargs)
