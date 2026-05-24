from __future__ import annotations


def decide_project(score: float, entry_window_count: int, confirmed_count: int, paper_enter_count: int) -> dict:
    if score >= 60 and entry_window_count > 0 and confirmed_count > 0 and paper_enter_count > 0:
        return {"project_decision": "CONTINUE", "live_readiness_opinion": "PAPER_MORE_REQUIRED", "reason": "Entry, confirmation, and paper evidence exist."}
    if score < 35 and entry_window_count == 0 and confirmed_count == 0 and paper_enter_count == 0:
        return {"project_decision": "KILL_RECOMMENDED", "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED", "reason": "No entry window, no confirmed state, and no paper enter after event collection."}
    return {"project_decision": "PAUSE", "live_readiness_opinion": "PROJECT_PAUSE_RECOMMENDED", "reason": "Collection works, but entry/confirmation evidence is insufficient."}
