from __future__ import annotations

from bear_window.bear_window_report_builder import router_decision


def test_v685_router_decision_accepts_window_metric_keys() -> None:
    active = {"bear_window_return": -5.0, "bear_window_mdd": -12.0}
    router = {"bear_window_return": -2.0, "bear_window_mdd": -9.0}
    assert router_decision(active, router) == "BEAR_ROUTER_V685_SHADOW_CANDIDATE"


def test_v685_router_decision_requires_forward_when_mdd_worse() -> None:
    active = {"bear_window_return": -5.0, "bear_window_mdd": -8.0}
    router = {"bear_window_return": -2.0, "bear_window_mdd": -12.0}
    assert router_decision(active, router) == "BEAR_ROUTER_NEEDS_FORWARD_PAPER"
