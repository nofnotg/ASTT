from __future__ import annotations

import os


def llm_config(provider: str = "openai") -> dict:
    return {"provider": provider, "api_key_present": bool(os.environ.get("OPENAI_API_KEY")), "api_key_value_stored": False}
