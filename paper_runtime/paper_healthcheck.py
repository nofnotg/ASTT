from __future__ import annotations


def paper_healthcheck() -> dict[str, str | bool]:
    return {"status": "PAPER_HEALTHY", "real_order_enabled": False, "live_order_allowed": False}
