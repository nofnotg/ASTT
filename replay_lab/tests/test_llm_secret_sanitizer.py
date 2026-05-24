from head_controller.llm_secret_sanitizer import sanitize_for_report, scan_report_secrets


def test_llm_secret_sanitizer_removes_keys_and_paths(tmp_path):
    data = {"openai_key_masked": "sk-a****bbbb", "path": r"C:\Users\me\OneDrive\바탕 화면\keys.txt", "nested": {"value": "AQ.Ab8secret"}}
    clean = sanitize_for_report(data)
    assert "openai_key_masked" not in clean
    assert "[REDACTED]" in str(clean)
    f = tmp_path / "latest_x.json"
    f.write_text(str(clean), encoding="utf-8")
    assert scan_report_secrets(tmp_path)["secret_scan_status"] == "PASS"
