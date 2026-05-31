from __future__ import annotations

from paper_runtime.paper_runtime_schema import safety_flags


def assert_live_orders_disabled() -> dict[str, bool | str]:
    flags = safety_flags()
    if flags["real_order_enabled"] or flags["live_order_allowed"]:
        raise RuntimeError("LIVE_ORDER_DISABLED")
    return {"live_order_guard": "ACTIVE", **flags}
