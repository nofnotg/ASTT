from head_controller.llm_config import build_head_controller_llm_config


def test_head_controller_llm_config_selects_openai_without_auto_apply(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("GPT: sk-openai-1234567890\n", encoding="utf-8")
    config = build_head_controller_llm_config("auto", str(key_file))
    assert config["selected_provider"] == "openai"
    assert config["llm_enabled"] is True
    assert config["auto_apply_allowed"] is False
    assert config["live_order_allowed"] is False
