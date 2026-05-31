from __future__ import annotations

from bear_response.bear_bounce_score import score_bear_bounce
from analysis.v682_bear_response_analyzer import register_v682_shadow_route


def test_bear_bounce_score_uses_available_context_without_live_flags() -> None:
    context = {
        "trade": {"plan": "PLAN_A_ICT_FAT_TAIL", "setup_type": "LIQUIDITY_SWEEP+FVG_OB_OVERLAP"},
        "state": {"market_state": "RISK_OFF_ALT_WEAK", "dominance_regime": "BTCDOM_STABLE", "btc_trend": "SIDEWAYS"},
        "feature": {"btcdom_delta_1h": -0.1, "btcdom_delta_4h": 0.1, "btcdom_delta_24h": 0.5},
        "btc": {"btc_structure": "RANGE"},
    }
    score = score_bear_bounce(context, [], guard_on=True, hard_guard=False, drawdown_pct=-12.0)

    assert score["bear_bounce_score"] >= 60
    assert score["bear_bounce_candidate"] is True
    assert score["bear_bounce_blocked"] is False
    assert "spread_depth" in score["missing_bounce_features"]


def test_lockdown_blocks_bear_bounce_candidate() -> None:
    context = {
        "trade": {"plan": "PLAN_A_ICT_FAT_TAIL", "setup_type": "LIQUIDITY_SWEEP+FVG_OB_OVERLAP"},
        "state": {"market_state": "LOCKDOWN", "dominance_regime": "BTCDOM_STABLE", "btc_trend": "SIDEWAYS"},
        "feature": {"btcdom_delta_1h": -0.1, "btcdom_delta_4h": 0.1, "btcdom_delta_24h": 0.5},
        "btc": {"btc_structure": "RANGE"},
    }
    score = score_bear_bounce(context, [], guard_on=True, hard_guard=True, drawdown_pct=-20.0)

    assert score["bear_bounce_blocked"] is True
    assert score["bear_bounce_candidate"] is False


def test_v682_shadow_registration_never_applies_active_change() -> None:
    payload = register_v682_shadow_route("FULL_BEAR_RESPONSE_ROUTER")

    assert payload["decision"] == "SHADOW_ROUTE_READY"
    assert payload["active_route_change_applied"] is False
    assert payload["real_order_enabled"] is False
    assert payload["live_order_allowed"] is False
    assert payload["auto_apply_allowed"] is False
