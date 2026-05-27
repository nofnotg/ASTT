from __future__ import annotations

from typing import Any


def audit_v67_data_quality(quality_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_period_validation_possible": bool(quality_summary.get("full_period_validation_possible")),
        "fake_data_generated": bool(quality_summary.get("fake_data_generated", False)),
        "missing_data": quality_summary.get("missing_data", []),
        "decision": "GOOD" if quality_summary.get("full_period_validation_possible") else "GLOBAL_BTCD_DATA_REQUIRED",
    }
