from __future__ import annotations


FORBIDDEN_READINESS = {"MICRO_LIVE_READY", "LIVE_READY"}


def enforce_head_controller_safety(output: dict) -> dict:
    output = dict(output)
    if output.get("live_readiness_opinion") in FORBIDDEN_READINESS:
        output["live_readiness_opinion"] = "LIVE_NOT_ALLOWED"
    output["auto_apply_allowed"] = False
    for proposal in output.get("config_proposals", []):
        proposal["active"] = False
        proposal["human_approved"] = False
    return output
