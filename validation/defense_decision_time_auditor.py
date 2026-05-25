from __future__ import annotations

from typing import Any


def audit_defense_decision_times(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    checked = 0
    for scenario in scenarios:
        for trade in scenario.get("annotated_trade_sample", []):
            checked += 1
            decision_time = str(trade.get("decision_time", ""))
            entry_time = str(trade.get("entry_time", ""))
            if decision_time > entry_time:
                failures.append({"scenario": scenario.get("scenario"), "trade_id": trade.get("trade_id"), "reason": "decision time is after entry time"})
    return {"check": "defense_decision_check", "status": "PASS" if not failures else "FAIL", "checked": checked, "failures": failures}
