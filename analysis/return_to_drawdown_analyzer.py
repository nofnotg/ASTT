from __future__ import annotations

from typing import Any


def add_return_to_drawdown_decisions(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for scenario in scenarios:
        capital = scenario.get("capital", {})
        ratio = float(capital.get("return_to_mdd_ratio", 0.0))
        mdd = abs(float(capital.get("max_drawdown_pct", 0.0)))
        ret = float(capital.get("total_return_pct", 0.0))
        if int(scenario.get("dd_cap_violations", 0)) > 0 or int(scenario.get("protected_floor_violations", 0)) > 0:
            decision = "TOO_RISKY"
        elif scenario.get("high_risk_research_only"):
            decision = "KEEP_AS_RESEARCH_ONLY" if ret > 0 and mdd <= 35 else "TOO_RISKY"
        elif ret > 0 and mdd <= 20 and ratio > 4:
            decision = "KEEP_FOR_FORWARD"
        elif ret > 0 and mdd <= 30:
            decision = "PAPER_MORE_REQUIRED"
        elif mdd > 35:
            decision = "TOO_RISKY"
        else:
            decision = "REJECT"
        rows.append({"scenario": scenario.get("scenario"), "return_to_mdd_ratio": ratio, "decision": decision})
    return rows
