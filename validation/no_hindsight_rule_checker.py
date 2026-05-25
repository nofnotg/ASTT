from __future__ import annotations

from typing import Any


FORBIDDEN_MARKERS = ["2025-05-13", "2026-04-12", "known_drawdown_period", "future_mdd"]


def check_no_hindsight_rules(payload: dict[str, Any]) -> dict[str, Any]:
    failures = []
    text = str(payload.get("causal_policy_notes", "")) + " " + str(payload.get("scenario_generation_notes", ""))
    for marker in FORBIDDEN_MARKERS:
        if marker in text:
            failures.append({"marker": marker, "reason": "policy text directly references known future drawdown"})
    return {"check": "no_hindsight_check", "status": "PASS" if not failures else "FAIL", "checked": len(FORBIDDEN_MARKERS), "failures": failures}
