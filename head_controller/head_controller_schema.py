from __future__ import annotations


def build_controller_output(primary_problem: str, next_experiments: list[str], risk_flags: list[str], config_proposals: list[dict] | None = None) -> dict:
    return {
        "controller_version": "v556_draft",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "primary_problem": primary_problem,
        "root_cause_hypotheses": risk_flags,
        "next_experiments": next_experiments,
        "risk_flags": risk_flags,
        "config_proposals": config_proposals or [],
        "auto_apply_allowed": False,
    }
