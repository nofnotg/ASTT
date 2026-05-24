from __future__ import annotations

import os
import re
from pathlib import Path


OPENAI_ENV_NAMES = ("OPENAI_API_KEY", "GPT_API_KEY")
GEMINI_ENV_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY")


def load_head_controller_llm_keys(key_file: str | None = None) -> dict:
    file_values = _load_key_file(key_file) if key_file else {}
    openai_key = _first_env_or_file(OPENAI_ENV_NAMES, file_values)
    gemini_key = _first_env_or_file(GEMINI_ENV_NAMES, file_values)
    return {
        "openai_key_loaded": bool(openai_key),
        "gemini_key_loaded": bool(gemini_key),
        "openai_key_masked": mask_secret(openai_key),
        "gemini_key_masked": mask_secret(gemini_key),
        "key_file_loaded": bool(key_file and Path(key_file).exists()),
        "key_file_path": str(key_file) if key_file else "",
        "secret_values_returned": False,
        "_openai_key": openai_key,
        "_gemini_key": gemini_key,
    }


def public_llm_key_status(status: dict) -> dict:
    return {k: v for k, v in status.items() if not k.startswith("_") and k != "key_file_path"}


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


def _first_env_or_file(names: tuple[str, ...], file_values: dict[str, str]) -> str:
    for name in names:
        value = os.environ.get(name) or file_values.get(name)
        if value and _looks_like_api_key(name, value.strip().strip('"').strip("'")):
            return value.strip().strip('"').strip("'")
    return ""


def _looks_like_api_key(name: str, value: str) -> bool:
    if len(value) < 20:
        return False
    upper = name.upper()
    if "OPENAI" in upper or "GPT" in upper:
        return value.startswith("sk-")
    if "GEMINI" in upper or "GOOGLE" in upper:
        return value.startswith("AIza") or value.startswith("AQ.") or len(value) >= 30
    return True


def _load_key_file(path: str) -> dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    values: dict[str, str] = {}
    pending_key = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if pending_key:
            values[pending_key] = line.strip().strip('"').strip("'")
            pending_key = ""
            continue
        match = re.match(r"^\$env:([A-Za-z0-9_]+)\s*=\s*[\"'](.+?)[\"']\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
            continue
        match = re.match(r"^([A-Za-z0-9_ ]+)\s*[:=]\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            key = _normalize_label(match.group(1))
            value = match.group(2).strip()
            if value:
                values[key] = value
            else:
                pending_key = key
            continue
        lowered = line.lower()
        if "openai" in lowered or "gpt" in lowered:
            values["OPENAI_API_KEY"] = line.split()[-1].strip().strip('"').strip("'")
        elif "gemini" in lowered or "google" in lowered:
            values["GEMINI_API_KEY"] = line.split()[-1].strip().strip('"').strip("'")
    return values


def _normalize_label(label: str) -> str:
    upper = label.upper().replace("-", "_").replace(" ", "_")
    compact = upper.replace("_", "")
    if upper in {"GPT", "GPT_KEY", "OPENAI", "OPENAI_KEY", "OPEN_AI_API_KEY", "OPEN_API_KEY"} or compact in {"OPENAI", "OPENAIKEY", "OPENAIAPIKEY", "OPENAPIKEY", "GPTAPIKEY"}:
        return "OPENAI_API_KEY"
    if upper in {"GEMINI", "GEMINI_KEY", "GOOGLE", "GOOGLE_KEY"} or compact in {"GEMINI", "GEMINIKEY", "GEMINIAPIKEY", "GOOGLEAPIKEY"}:
        return "GEMINI_API_KEY"
    return upper
