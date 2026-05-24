import json

from artifact_integrity.report_artifact_manifest import build_artifact_manifest
from artifact_integrity.report_artifact_validator import validate_report_artifacts


def test_report_artifact_validator_detects_test_artifact(tmp_path):
    summary = {"candidate_count": 1, "live_readiness": "LIVE_NOT_ALLOWED", "artifact_manifest": build_artifact_manifest("ENTRY_DISCOVERY", "s", 1, [], 0, "TEST", True)}
    (tmp_path / "latest_entry_discovery_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    result = validate_report_artifacts(tmp_path)
    assert result["artifact_integrity_status"] == "FAIL"
    assert result["stale_or_test_artifact_detected"] is True
