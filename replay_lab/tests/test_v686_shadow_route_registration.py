from __future__ import annotations

from analysis.v686_core import build_v686_shadow_route_registration_payload


def test_v686_shadow_registration_does_not_change_active() -> None:
    payload = build_v686_shadow_route_registration_payload()
    assert payload["v685_router_registered"] is True
    assert payload["active_changed"] is False
    assert "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW" in payload["shadow_routes"]
