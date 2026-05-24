from __future__ import annotations

from head_controller.head_controller_safety_guard import enforce_head_controller_safety


def sanitize_llm_controller_output(output: dict) -> dict:
    safe = enforce_head_controller_safety(output)
    safe["llm_output_sanitized"] = True
    return safe
