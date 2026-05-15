from __future__ import annotations

from decision.debate_engine import FinalDecision


def assert_can_create_intent(decision: FinalDecision) -> None:
    if decision.vetoed:
        raise RuntimeError(f"OrderIntent blocked by Iris veto: {decision.veto_reason}")
    if decision.decision != "ENTER":
        raise RuntimeError(f"OrderIntent blocked because final decision is {decision.decision}")

