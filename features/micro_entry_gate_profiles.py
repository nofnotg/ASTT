from __future__ import annotations


GATE_PROFILES = {
    "STRICT": {
        "min_buy_trade_ratio_5s": 0.55,
        "allow_micro_state": ["ACCELERATING"],
        "max_cost_to_target_ratio": 0.30,
        "require_orderbook": True,
        "research_only": False,
    },
    "BALANCED": {
        "min_buy_trade_ratio_5s": 0.50,
        "allow_micro_state": ["ACCELERATING", "STABLE"],
        "max_cost_to_target_ratio": 0.40,
        "require_orderbook": False,
        "research_only": False,
    },
    "EXPLORATORY": {
        "min_buy_trade_ratio_5s": 0.48,
        "allow_micro_state": ["ACCELERATING", "STABLE", "FADING"],
        "max_cost_to_target_ratio": 0.50,
        "require_orderbook": False,
        "research_only": True,
    },
}


def get_gate_profile(name: str) -> dict:
    key = name.upper()
    if key not in GATE_PROFILES:
        raise ValueError(f"unknown gate profile: {name}")
    return dict(GATE_PROFILES[key])


def list_gate_profiles() -> dict:
    return {key: dict(value) for key, value in GATE_PROFILES.items()}
