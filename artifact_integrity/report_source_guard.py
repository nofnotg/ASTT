from __future__ import annotations

from artifact_integrity.report_artifact_validator import validate_report_artifacts


def guard_reports_for_head_controller(reports_dir: str) -> dict:
    result = validate_report_artifacts(reports_dir)
    return {"allowed": result["artifact_integrity_status"] != "FAIL", "validation": result}
