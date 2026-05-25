from __future__ import annotations


def score_ma_quality(states: list[str]) -> tuple[float, list[str]]:
    score = 60.0
    reasons: list[str] = []
    positive = {
        "MA_BULL": 15,
        "MA_RECLAIM_20": 10,
        "MA_SQUEEZE_BREAKOUT": 20,
        "TESTA_BULL_ALIGNMENT": 15,
        "TESTA_RECLAIM_5": 8,
        "TESTA_SUPPORT_25": 8,
        "TESTA_STRONG_SLOPE": 8,
    }
    negative = {
        "MA_CHOP": -30,
        "MA_BEAR": -40,
        "MA_OVEREXTENDED": -20,
        "TESTA_LOST_75": -45,
        "TESTA_CHOP": -20,
        "TESTA_BEAR_ALIGNMENT": -35,
        "TESTA_WEAK_SLOPE": -8,
    }
    for state, delta in positive.items():
        if state in states:
            score += delta
            reasons.append(f"{state} +{delta}")
    for state, delta in negative.items():
        if state in states:
            score += delta
            reasons.append(f"{state} {delta}")
    return max(0.0, min(100.0, score)), reasons
