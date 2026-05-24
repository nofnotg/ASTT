from replay_lab.research.artifact_integrity_check_v5561 import scan_report_secrets_v5561


def test_openai_key_never_written_to_reports():
    result = scan_report_secrets_v5561("docs/reports")
    assert result["secret_scan_status"] == "PASS"
    assert result["raw_secret_detected"] is False
    assert result["masked_secret_detected"] is False
    assert result["key_path_detected"] is False
