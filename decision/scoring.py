from __future__ import annotations

DEFAULT_WEIGHTS = {
    "Mr.K": 0.10,
    "매기": 0.30,
    "Rezo": 0.25,
    "CostA": 0.10,
    "Iris": 0.25,
}


def weighted_score(results: list, weights: dict[str, float] | None = None) -> float:
    weights = weights or DEFAULT_WEIGHTS
    score = 0.0
    weight_total = 0.0
    for result in results:
        weight = weights.get(result.persona_name, 0.0)
        score += float(result.score) * weight
        weight_total += weight
    if weight_total == 0:
        return 0.0
    return round(score / weight_total, 2)

