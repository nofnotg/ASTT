from __future__ import annotations

from collections import Counter

from features.micro_entry_gate_profiles import get_gate_profile


def run_micro_entry_gate_abtest(candidates: list[dict], profile_names=("STRICT", "BALANCED", "EXPLORATORY"), cost_scenario: str = "realistic_1") -> dict:
    profiles = {}
    for name in profile_names:
        profile = get_gate_profile(name)
        entered = []
        waited = []
        canceled = []
        for candidate in candidates:
            decision = _profile_decision(candidate, profile)
            if decision == "ENTER":
                entered.append(candidate)
            elif decision == "CANCEL":
                canceled.append(candidate)
            else:
                waited.append(candidate)
        profiles[name] = {
            "candidate_count": len(candidates),
            "enter_count": len(entered),
            "wait_count": len(waited),
            "cancel_count": len(canceled),
            "pf_realistic_1": 0.0,
            "expectancy_realistic_1": 0.0,
            "research_only": profile["research_only"],
            "block_reason_counts": dict(Counter(candidate.get("primary_block_reason", "UNKNOWN_BLOCK") for candidate in waited + canceled)),
        }
    return {"cost_scenario": cost_scenario, "profiles": profiles}


def _profile_decision(candidate: dict, profile: dict) -> str:
    if candidate.get("data_quality") in {"POOR", "UNAVAILABLE"}:
        return "CANCEL"
    if profile.get("require_orderbook") and "ORDERBOOK_UNAVAILABLE" in candidate.get("block_reasons", []):
        return "WAIT"
    ratio = candidate.get("gate_values", {}).get("cost_to_target_ratio")
    if ratio is not None and ratio > profile["max_cost_to_target_ratio"]:
        return "WAIT"
    state = candidate.get("gate_values", {}).get("micro_state")
    if state in profile["allow_micro_state"] and candidate.get("primary_block_reason") not in {"DATA_QUALITY_POOR", "COST_TO_TARGET_TOO_HIGH", "TARGET_TOO_SMALL"}:
        return "ENTER"
    if profile["research_only"] and candidate.get("primary_block_reason") in {"MICRO_STATE_WEAK", "BUY_TRADE_RATIO_LOW", "UNKNOWN_BLOCK"}:
        return "ENTER"
    return "WAIT"
