from artifact_integrity.report_artifact_manifest import build_artifact_manifest


def test_report_artifact_manifest_marks_candidate_count():
    m = build_artifact_manifest("ENTRY_DISCOVERY", "sessions", 49, ["s1"], 10)
    assert m["artifact_integrity_status"] == "PASS"
    assert m["is_test_artifact"] is False


def test_report_artifact_manifest_fails_test_artifact():
    m = build_artifact_manifest("ENTRY_DISCOVERY", "sessions", 1, [], 0, generated_by="TEST", is_test_artifact=True)
    assert m["artifact_integrity_status"] == "FAIL"
