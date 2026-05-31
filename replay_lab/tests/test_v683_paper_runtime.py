from __future__ import annotations

import pytest

from paper_runtime.live_order_adapter_stub import LiveOrderAdapterStub
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_route_registry import route_registry, switch_active_route


def test_v683_route_registry_defaults_are_paper_locked() -> None:
    registry = route_registry()

    assert registry["active_route"] == "LG_V2_BALANCED_PLUS_DOM_GATE"
    assert "LG_M3_PF0.8_DD8" in registry["shadow_routes"]
    assert registry["route_switch_locked"] is True
    assert registry["active_auto_switch_allowed"] is False
    assert registry["real_order_enabled"] is False
    assert registry["live_order_allowed"] is False


def test_v683_switch_requires_confirm_switch() -> None:
    result = switch_active_route("LG_M3_PF0.8_DD8", confirm_switch=False)

    assert result["switched"] is False
    assert result["decision"] == "MANUAL_APPROVAL_REQUIRED"
    assert result["real_order_enabled"] is False


def test_v683_live_order_guard_and_stub_block_orders() -> None:
    assert assert_live_orders_disabled()["live_order_guard"] == "ACTIVE"
    with pytest.raises(RuntimeError, match="LIVE_ORDER_DISABLED"):
        LiveOrderAdapterStub().buy("KRW-BTC", 1000)
