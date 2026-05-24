import json

from artifact_integrity.report_artifact_manifest import build_artifact_manifest
from head_controller.head_controller_context_builder import build_head_controller_context
from head_controller.head_controller_analyzer import analyze_head_controller_context


def test_report_source_guard_blocks_head_controller(tmp_path):
    summary = {"candidate_count": 1, "live_readiness": "LIVE_NOT_ALLOWED", "artifact_manifest": build_artifact_manifest("ENTRY_DISCOVERY", "s", 1, [], 0)}
    (tmp_path / "latest_entry_discovery_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    result = analyze_head_controller_context(build_head_controller_context(tmp_path))
    assert result["primary_problem"] == "ARTIFACT_INTEGRITY_FAIL"
    assert result["config_proposals"] == []
