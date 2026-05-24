from __future__ import annotations

import json


def compress_context(context: dict, max_chars: int = 12000) -> str:
    text = json.dumps(context, ensure_ascii=False, sort_keys=True)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated for token budget]"
