from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


MARKET_STATES = (
    "BULL_ATTACK",
    "ALT_FRIENDLY",
    "NORMAL",
    "BTC_LED_MARKET",
    "EDGE_DECAY",
    "RISK_OFF_ALT_WEAK",
    "BEAR_DEFENSE",
    "BEAR_BOUNCE_ONLY",
    "LOCKDOWN",
)

SCENARIO_NAMES = (
    "ROLLING_ONLY_CONTROL",
    "ROLLING_ONLY_DOMINANCE_OVERLAY",
    "BALANCED_ONLY_CONTROL",
    "BALANCED_ONLY_DOMINANCE_OVERLAY",
    "POLICY_BLEND_CONTROL",
    "POLICY_BLEND_DOMINANCE_OVERLAY",
    "RELATIVE_STRENGTH_BEAR_AGENT",
    "BEAR_DEFENSE_AGENT",
    "CASH_DEFENSE_AGENT",
    "BEAR_BOUNCE_V2_RESEARCH_AGENT",
    "SCENARIO_AGENT_ROUTER_V1",
)


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    final_equity_krw: float | None
    total_return_pct: float | None
    mdd_pct: float | None
    profit_factor: float | None
    trade_count: int
    decision: str
    return_mdd_ratio: float | None = None
    saved_loss_krw: float = 0.0
    missed_profit_krw: float = 0.0
    net_effect_krw: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def safe_flags() -> dict[str, bool]:
    return {
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
