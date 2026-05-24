from __future__ import annotations


def build_config_proposal(profile: str, reason: str) -> dict:
    return {"proposal_id": f"v556_{profile.lower()}", "profile": profile, "reason": reason, "active": False, "human_approved": False}
