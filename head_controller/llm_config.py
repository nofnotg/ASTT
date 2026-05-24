from __future__ import annotations

from head_controller.llm_key_loader import load_head_controller_llm_keys, public_llm_key_status


def build_head_controller_llm_config(provider: str = "auto", key_file: str | None = None) -> dict:
    status = load_head_controller_llm_keys(key_file)
    public = public_llm_key_status(status)
    selected = "off"
    if provider == "openai" and status["_openai_key"]:
        selected = "openai"
    elif provider == "gemini" and status["_gemini_key"]:
        selected = "gemini"
    elif provider == "auto":
        selected = "openai" if status["_openai_key"] else ("gemini" if status["_gemini_key"] else "off")
    elif provider == "off":
        selected = "off"
    return {
        **public,
        "requested_provider": provider,
        "selected_provider": selected,
        "llm_enabled": selected != "off",
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
