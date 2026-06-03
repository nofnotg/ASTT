from __future__ import annotations

from scenario_telemetry.v688_common import safe_status


def test_v688_safety_flags_are_locked() -> None:
    status = safe_status()
    assert status["real_order_enabled"] is False
    assert status["live_order_allowed"] is False
    assert status["auto_apply_allowed"] is False
    assert status["order_api_called"] is False
    assert status["manual_review_required"] is True
