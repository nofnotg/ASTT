from __future__ import annotations

from winner_mining.missed_winner_analyzer import analyze_missed_winners


def analyze_missed_winners_v558(winner_traces: str = "replay_store/winner_mining/traces") -> dict:
    return analyze_missed_winners(winner_traces)
