from __future__ import annotations


REQUIRED_FIELDS = {
    "strategy_id",
    "source_id",
    "source_url",
    "license_status",
    "strategy_family",
    "timeframes",
    "indicators",
    "entry_rules",
    "exit_rules",
    "risk_rules",
    "market_regime_rules",
    "micro_execution_required",
    "notes",
}

VALID_LICENSE = {"OK", "REVIEW_REQUIRED", "DO_NOT_USE"}


def validate_strategy_spec(spec: dict) -> dict:
    missing = sorted(REQUIRED_FIELDS - set(spec))
    warnings = []
    if spec.get("license_status") not in VALID_LICENSE:
        warnings.append("invalid_license_status")
    if not spec.get("strategy_id"):
        warnings.append("missing_strategy_id")
    if not isinstance(spec.get("indicators", []), list):
        warnings.append("indicators_must_be_list")
    valid = not missing and not warnings
    return {"valid": valid, "missing_fields": missing, "warnings": warnings}
