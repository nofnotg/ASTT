from __future__ import annotations

from typing import Any


def api_response(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": data}
