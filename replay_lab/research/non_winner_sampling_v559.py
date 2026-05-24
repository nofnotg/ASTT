from __future__ import annotations

from winner_mining.non_winner_sampler import sample_non_winners


def run_non_winner_sampling_v559(sessions_dir: str, sample_ratio: float = 2.0) -> dict:
    return sample_non_winners(sessions_dir, sample_ratio)
