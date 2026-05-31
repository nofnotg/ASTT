from __future__ import annotations

from analysis.v686_core import build_v686_control_tower_dashboard_payload


def test_v686_control_tower_is_manual_review_only(tmp_path) -> None:
    payload = build_v686_control_tower_dashboard_payload(tmp_path)
    assert payload["fallback_used"] is True
    assert payload["active_change_applied"] is False
    assert payload["live_order_allowed"] is False
