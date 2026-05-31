from __future__ import annotations


def daemon_status() -> dict[str, bool | str]:
    return {"paper_daemon_ready": True, "live_forward_running": False, "real_order_enabled": False, "live_order_allowed": False}
