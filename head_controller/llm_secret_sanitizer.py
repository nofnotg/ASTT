from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

FORBIDDEN_KEYS = {"openai_key_masked", "gemini_key_masked", "key_file_path", "_openai_key", "_gemini_key"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AQ\.[A-Za-z0-9_\-\.]{8,}"),
    re.compile(r"[A-Za-z]:\\Users\\[^\"'\s]+"),
    re.compile(r"OneDrive|바탕 화면"),
]


def sanitize_for_report(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sanitize_for_report(v) for k, v in value.items() if k not in FORBIDDEN_KEYS}
    if isinstance(value, list):
        return [sanitize_for_report(v) for v in value]
    if isinstance(value, str):
        cleaned = value
        for pattern in SECRET_PATTERNS:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        return cleaned
    return value


def scan_report_secrets(reports_dir: str | Path) -> dict:
    failures: list[str] = []
    files_checked: list[str] = []
    for path in Path(reports_dir).glob("latest_*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".html"}:
            files_checked.append(str(path))
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS) or any(key in text for key in FORBIDDEN_KEYS):
                failures.append(str(path))
    return {
        "secret_scan_status": "FAIL" if failures else "PASS",
        "raw_secret_detected": bool(failures),
        "masked_secret_detected": bool(failures),
        "key_path_detected": bool(failures),
        "files_checked": files_checked,
        "failures": failures,
    }


def dumps_sanitized(value: Any) -> str:
    return json.dumps(sanitize_for_report(value), ensure_ascii=False, indent=2, default=str)
