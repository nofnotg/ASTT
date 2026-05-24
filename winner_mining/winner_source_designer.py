from __future__ import annotations


def design_winner_sources(patterns: list[dict]) -> list[dict]:
    return [
        {
            "candidate_source": pattern["pattern_id"],
            "pattern_basis": pattern["pattern_id"],
            "support_count": pattern.get("support_count", 0),
            "false_positive_risk": pattern.get("false_positive_risk", "HIGH"),
            "research_mode": True,
            "real_order_enabled": False,
            "auto_apply_allowed": False,
        }
        for pattern in patterns
    ]
