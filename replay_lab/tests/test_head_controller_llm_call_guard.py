import json

from artifact_integrity.report_artifact_manifest import build_artifact_manifest
from head_controller.llm_call_guard import run_guarded_llm_analysis


def test_llm_call_guard_fallbacks_on_artifact_fail(tmp_path):
    summary = {"candidate_count": 1, "live_readiness": "LIVE_NOT_ALLOWED", "artifact_manifest": build_artifact_manifest("ENTRY_DISCOVERY", "s", 1, [], 0)}
    (tmp_path / "latest_entry_discovery_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    result = run_guarded_llm_analysis(str(tmp_path), "off")
    assert result["fallback_used"] is True
    assert result["call_success"] is False
