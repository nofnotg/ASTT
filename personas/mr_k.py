from __future__ import annotations

from personas.base import PersonaResult, decision_from_score


def analyze(context: dict) -> PersonaResult:
    market = context.get("market", "KRW-BTC")
    regime = context.get("regime", {})
    score = float(regime.get("score", 50))
    state = regime.get("state", "neutral")
    reasons = [f"market regime is {state}", f"regime score {score:.1f}"]
    return PersonaResult(
        persona_name="Mr.K",
        market=market,
        score=score,
        decision=decision_from_score(score, 65),
        reasons=reasons,
        payload={"regime": regime},
    )

