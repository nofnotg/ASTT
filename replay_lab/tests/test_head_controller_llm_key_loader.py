from head_controller.llm_key_loader import load_head_controller_llm_keys, public_llm_key_status


def test_head_controller_llm_key_loader_masks_file_values(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text('OPENAI_API_KEY="sk-test-openai-1234"\nGEMINI_API_KEY="gemini-test-5678"\n', encoding="utf-8")
    status = load_head_controller_llm_keys(str(key_file))
    public = public_llm_key_status(status)
    assert public["openai_key_loaded"] is True
    assert public["gemini_key_loaded"] is True
    assert "key_file_path" not in public
    assert "sk-test-openai-1234" not in str(public)
    assert public["secret_values_returned"] is False


def test_head_controller_llm_key_loader_supports_label_then_next_line(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("Open AI API Key:\nopenai-example-value\n\nGemini API Key:\ngemini-example-value\n", encoding="utf-8")
    public = public_llm_key_status(load_head_controller_llm_keys(str(key_file)))
    assert public["openai_key_loaded"] is True
    assert public["gemini_key_loaded"] is True
    assert "openai-example-value" not in str(public)
