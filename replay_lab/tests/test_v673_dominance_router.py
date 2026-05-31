from __future__ import annotations

from analysis.v673_rejected_scenario_cleaner import build_v673_rejection_report
from dominance_router.market_state_classifier import classify_market_state
from dominance_router.scenario_agent_router import select_agent


def test_v673_market_state_classifier_uses_dominance_direction():
    state = classify_market_state({"dominance_regime": "DOM_SPIKE", "dominance_delta_7d": 3.0}, {"btc_return_7d_pct": -2.0})

    assert state["market_state"] == "RISK_OFF_ALT_WEAK"


def test_v673_router_maps_risk_off_to_bear_defense():
    assert select_agent("RISK_OFF_ALT_WEAK") == "BEAR_DEFENSE_AGENT"
    assert select_agent("LOCKDOWN") == "OBSERVATION_ONLY"


def test_v673_rejection_report_keeps_only_candidate_decisions():
    report = build_v673_rejection_report(
        {
            "scenarios": [
                {"scenario": "POLICY_BLEND_CONTROL", "decision": "BASELINE"},
                {"scenario": "SCENARIO_AGENT_ROUTER_V1", "decision": "SCENARIO_AGENT_ROUTER_CANDIDATE"},
                {"scenario": "BEAR_BOUNCE_V2_RESEARCH_AGENT", "decision": "RESEARCH_ONLY"},
            ]
        }
    )

    assert report["kept_candidates"][0]["scenario"] == "SCENARIO_AGENT_ROUTER_V1"
    assert report["rejected_scenarios"][0]["scenario"] == "BEAR_BOUNCE_V2_RESEARCH_AGENT"
    assert report["live_order_allowed"] is False
