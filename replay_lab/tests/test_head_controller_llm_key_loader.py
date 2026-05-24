from head_controller.llm_key_loader import load_head_controller_llm_keys, public_llm_key_status


def test_head_controller_llm_key_loader_masks_file_values(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text('OPENAI_API_KEY="sk-test-openai-123456789012345"\nGEMINI_API_KEY="AIza-test-gemini-123456789012345"\n', encoding="utf-8")
    status = load_head_controller_llm_keys(str(key_file))
    public = public_llm_key_status(status)
    assert public["openai_key_loaded"] is True
    assert public["gemini_key_loaded"] is True
    assert "key_file_path" not in public
    assert "sk-test-openai-123456789012345" not in str(public)
    assert public["secret_values_returned"] is False


def test_head_controller_llm_key_loader_supports_label_then_next_line(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("Open AI API Key:\nsk-openai-example-value-1234567890\n\nGemini API Key:\nAIza-gemini-example-value-1234567890\n", encoding="utf-8")
    public = public_llm_key_status(load_head_controller_llm_keys(str(key_file)))
    assert public["openai_key_loaded"] is True
    assert public["gemini_key_loaded"] is True
    assert "sk-openai-example-value-1234567890" not in str(public)


def test_head_controller_llm_key_loader_rejects_status_text(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("OpenAI key loaded: true\nGemini key loaded: false\n", encoding="utf-8")
    public = public_llm_key_status(load_head_controller_llm_keys(str(key_file)))
    assert public["openai_key_loaded"] is False
    assert public["gemini_key_loaded"] is False
