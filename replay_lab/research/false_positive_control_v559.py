from __future__ import annotations

from winner_mining.false_positive_analyzer import analyze_false_positives


def run_false_positive_control_v559(quality_winners: str, non_winners: str, sources: str) -> dict:
    return analyze_false_positives(quality_winners, non_winners, sources)
