from __future__ import annotations


def score_ict_setup(confluence: dict, mtf_score: float) -> float:
    return float(max(0.0, min(100.0, confluence.get("quality_score", 0.0) * 0.8 + mtf_score * 0.2)))
