from __future__ import annotations

from datetime import datetime
from pathlib import Path


def build_artifact_manifest(
    artifact_type: str,
    source_sessions_dir: str | Path,
    candidate_count: int,
    source_session_ids: list[str] | None = None,
    source_event_count: int = 0,
    generated_by: str = "CLI",
    is_test_artifact: bool = False,
    min_expected_candidate_count: int = 30,
) -> dict:
    warnings: list[str] = []
    status = "PASS"
    if is_test_artifact or generated_by == "TEST":
        status = "FAIL"
        warnings.append("TEST_ARTIFACT")
    if candidate_count < min_expected_candidate_count:
        status = "FAIL"
        warnings.append("CANDIDATE_COUNT_BELOW_MINIMUM")
    return {
        "schema_version": "1.0",
        "artifact_type": artifact_type,
        "generated_at": datetime.now().isoformat(),
        "generated_by": generated_by,
        "source_sessions_dir": str(source_sessions_dir),
        "source_session_ids": source_session_ids or [],
        "source_event_count": source_event_count,
        "candidate_count": candidate_count,
        "is_test_artifact": is_test_artifact,
        "is_production_artifact": not is_test_artifact,
        "min_expected_candidate_count": min_expected_candidate_count,
        "artifact_integrity_status": status,
        "warnings": warnings,
    }
