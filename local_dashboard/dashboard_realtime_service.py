from __future__ import annotations


def polling_config() -> dict[str, int | bool]:
    return {"polling_enabled": True, "interval_ms": 5000, "websocket_enabled": False}
