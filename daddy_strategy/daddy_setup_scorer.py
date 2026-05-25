from __future__ import annotations


def score_daddy_setup(volume: dict, ma20: dict, neckline: dict, sr_flip: dict, fib: dict, mtf_score: float) -> float:
    score = (
        volume.get("score", 0.0) * 0.25
        + ma20.get("score", 0.0) * 0.2
        + neckline.get("score", 0.0) * 0.2
        + sr_flip.get("score", 0.0) * 0.2
        + fib.get("score", 0.0) * 0.1
        + mtf_score * 0.05
    )
    return float(max(0.0, min(100.0, score)))
