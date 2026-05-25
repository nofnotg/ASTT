from __future__ import annotations

from dataclasses import dataclass
from typing import Any


AMPLIFIABLE_STRATEGIES = {"ICT_FVG_OB_SWEEP", "COMBINED_VOLUME_ICT"}
AMPLIFIABLE_SETUPS = {"FVG_LIQUIDITY_SWEEP", "FVG_OB_OVERLAP", "DADDY_CONTEXT+FVG_OB_OVERLAP"}


@dataclass(frozen=True)
class ScenarioPolicy:
    name: str
    decision: str
    high_risk_research_only: bool = False


SCENARIO_POLICIES: dict[str, ScenarioPolicy] = {
    "BASELINE": ScenarioPolicy("BASELINE", "REFERENCE_ONLY"),
    "DRAWDOWN_THROTTLE": ScenarioPolicy("DRAWDOWN_THROTTLE", "REFERENCE_ONLY"),
    "ROLLING_EDGE_THROTTLE": ScenarioPolicy("ROLLING_EDGE_THROTTLE", "DEFENSE_VALIDATED_CANDIDATE"),
    "HYBRID_DEFENSE": ScenarioPolicy("HYBRID_DEFENSE", "DEFENSE_VALIDATED_CANDIDATE"),
    "DEFENSIVE_CORE": ScenarioPolicy("DEFENSIVE_CORE", "DEFENSIVE_FORWARD_CANDIDATE"),
    "BALANCED_GROWTH": ScenarioPolicy("BALANCED_GROWTH", "KEEP_FOR_FORWARD"),
    "AGGRESSIVE_GROWTH": ScenarioPolicy("AGGRESSIVE_GROWTH", "RETURN_AMPLIFICATION_CANDIDATE"),
    "HIGH_OCTANE_RESEARCH": ScenarioPolicy("HIGH_OCTANE_RESEARCH", "KEEP_AS_RESEARCH_ONLY", True),
}


def is_amplifiable_trade(trade: dict[str, Any]) -> bool:
    strategy = str(trade.get("strategy", ""))
    setup = str(trade.get("setup_type", ""))
    plan = str(trade.get("plan", ""))
    regime = str(trade.get("regime", ""))
    if regime in {"CHOP", "RISK_OFF", "NO_TRADE"}:
        return False
    return strategy in AMPLIFIABLE_STRATEGIES and setup in AMPLIFIABLE_SETUPS and plan in {"PLAN_A_ICT_FAT_TAIL", "PLAN_B_COMBINED_CONTEXT"}
