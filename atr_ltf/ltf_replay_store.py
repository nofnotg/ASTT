from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_ltf_cache_index(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "fake_data_generated": False}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def read_ltf_cache_index(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    return json.loads(source.read_text(encoding="utf-8-sig")) if source.exists() else {}
