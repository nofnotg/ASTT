from __future__ import annotations

from bear_validation.bear_bounce_v3_score import score_bear_bounce_v3
from bear_validation.bear_router_v684 import route_for_state
from bear_validation.bear_window_detector import detect_bear_windows
from bear_validation.indicator_effectiveness_analyzer import indicator_rows
from paper_runtime.paper_runtime_schema import safety_flags


def test_v684_bear_window_detector_flags_monthly_loss() -> None:
    journal = [
        {"date": "2026-02-01", "entry_time": "2026-02-01", "exit_time": "2026-02-01", "equity_before": 100.0, "equity_after": 98.0, "pnl_krw": -2.0, "drawdown_pct": -2.0, "defense_action": "ENTER", "market_state": "NORMAL"},
        {"date": "2026-02-02", "entry_time": "2026-02-02", "exit_time": "2026-02-02", "equity_before": 98.0, "equity_after": 95.0, "pnl_krw": -3.0, "drawdown_pct": -5.0, "defense_action": "ENTER", "market_state": "RISK_OFF_ALT_WEAK"},
    ]
    windows = detect_bear_windows(journal)
    assert windows
    assert windows[0]["recommended_test_group"] in {"LOSS_GUARD_INDICATOR_LAB", "BEAR_ROUTER_LAB"}


def test_v684_bear_bounce_v3_is_research_only_signal() -> None:
    context = {"trade": {"setup_type": "SWEEP_REVERSAL", "plan": "PLAN_A_ICT_FAT_TAIL", "return_pct": 1.0}, "state": {"market_state": "RISK_OFF_ALT_WEAK", "btc_trend": "SIDEWAYS", "dominance_regime": "BTCDOM_FALLING"}}
    score = score_bear_bounce_v3(context, {"drawdown_pct": -10.0, "hard_guard": True})
    assert score["bear_bounce_v3_candidate"] is True
    assert safety_flags()["live_order_allowed"] is False


def test_v684_indicator_and_router_are_paper_locked() -> None:
    rows = indicator_rows([{"pnl_krw": -100.0, "market_state": "RISK_OFF_ALT_WEAK", "dominance_regime": "BTCDOM_SPIKE", "defense_action": "ENTER"}])
    assert rows[0]["decision"] in {"INDICATOR_CANDIDATE", "RESEARCH_ONLY"}
    assert route_for_state({"market_state": "LOCKDOWN"})["route"] == "OBSERVE_ONLY"
    assert safety_flags()["real_order_enabled"] is False
