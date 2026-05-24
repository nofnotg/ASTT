from __future__ import annotations

import json


def parse_schema_completion(text: str, required_keys: list[str] | None = None) -> dict:
    required_keys = required_keys or ["summary", "live_readiness_opinion", "auto_apply_allowed", "live_order_allowed"]
    try:
        row = json.loads(text)
    except Exception:
        return {"schema_valid": False, "parsed": {}, "error": "JSON_PARSE_FAILED"}
    missing = [key for key in required_keys if key not in row]
    row["auto_apply_allowed"] = False
    row["live_order_allowed"] = False
    return {"schema_valid": not missing, "parsed": row, "error": "MISSING_KEYS" if missing else ""}
