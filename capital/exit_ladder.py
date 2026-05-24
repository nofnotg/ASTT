from __future__ import annotations


def build_exit_ladder(profile: str = "BALANCED") -> dict:
    if profile == "BREAKOUT":
        targets = [(1, 0.5, 1.0), (2, 0.3, 2.0), (3, 0.2, None)]
    elif profile == "PULLBACK":
        targets = [(1, 0.5, 0.5), (2, 0.3, 0.9), (3, 0.2, None)]
    else:
        targets = [(1, 0.5, 0.4), (2, 0.3, 0.7), (3, 0.2, None)]
    return {
        "exit_plan": [
            {"step": step, "pct": pct, **({"target_pct": target} if target is not None else {"mode": "TRAILING"})}
            for step, pct, target in targets
        ]
    }
