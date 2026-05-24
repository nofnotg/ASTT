from __future__ import annotations

from winner_mining.source_discriminative_power import analyze_source_discriminative_power


def run_source_discriminative_power_v559(quality_winners: str, non_winners: str) -> dict:
    return analyze_source_discriminative_power(quality_winners, non_winners)
