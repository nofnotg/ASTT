from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PersonaResult(BaseModel):
    persona_name: str
    market: str
    score: float = Field(ge=0, le=100)
    decision: str
    reasons: list[str]
    warnings: list[str] = []
    veto: bool = False
    veto_reason: str | None = None
    payload: dict[str, Any] = {}


def decision_from_score(score: float, pass_score: float = 80) -> str:
    if score >= pass_score:
        return "PASS"
    if score >= 60:
        return "WATCH"
    return "REJECT"

