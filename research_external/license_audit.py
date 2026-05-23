from __future__ import annotations


def audit_strategy_license(strategy_spec: dict) -> dict:
    status = strategy_spec.get("license_status", "REVIEW_REQUIRED")
    return {
        "strategy_id": strategy_spec.get("strategy_id"),
        "license_status": status,
        "usable_for_research": status in {"OK", "REVIEW_REQUIRED"},
        "code_copy_allowed": False,
        "warnings": ["manual_license_review_required"] if status == "REVIEW_REQUIRED" else [],
    }
