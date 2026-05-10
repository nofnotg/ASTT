from __future__ import annotations

from pydantic import BaseModel

from app.config import Settings, get_settings
from decision.scoring import DEFAULT_WEIGHTS, weighted_score
from personas.base import PersonaResult


class FinalDecision(BaseModel):
    market: str
    final_score: float
    decision: str
    vetoed: bool
    veto_reason: str | None
    reasons: list[str]
    persona_results: list[PersonaResult]


def decide(market: str, persona_results: list[PersonaResult], settings: Settings | None = None, weights: dict[str, float] | None = None) -> FinalDecision:
    settings = settings or get_settings()
    veto = next((item for item in persona_results if item.veto), None)
    final_score = weighted_score(persona_results, weights or DEFAULT_WEIGHTS)
    reasons: list[str] = []
    for result in sorted(persona_results, key=lambda item: item.score, reverse=True):
        if result.reasons:
            reasons.append(f"{result.persona_name}: {result.reasons[0]}")
    while len(reasons) < 3:
        reasons.append("insufficient additional persona reasons")
    if veto:
        return FinalDecision(market=market, final_score=final_score, decision="REJECT", vetoed=True, veto_reason=veto.veto_reason, reasons=reasons[:3], persona_results=persona_results)
    if final_score >= settings.min_final_score:
        decision = "ENTER"
    elif final_score >= 60:
        decision = "WATCH"
    else:
        decision = "REJECT"
    return FinalDecision(market=market, final_score=final_score, decision=decision, vetoed=False, veto_reason=None, reasons=reasons[:3], persona_results=persona_results)

