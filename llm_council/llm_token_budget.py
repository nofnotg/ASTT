from __future__ import annotations


def token_budget(review_type: str) -> dict:
    limits = {"daily": 2500, "weekly": 5000, "monthly": 6500, "research": 4500}
    return {"review_type": review_type, "max_input_tokens": limits.get(review_type, 2500), "raw_log_allowed": False}
