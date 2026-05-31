from __future__ import annotations

from local_dashboard.dashboard_security import is_forbidden_path, security_status


def test_v686_dashboard_has_no_live_order_endpoints() -> None:
    status = security_status()
    assert status["live_order_endpoints_enabled"] is False
    assert status["real_order_enabled"] is False
    assert is_forbidden_path("/api/orders/test") is True
