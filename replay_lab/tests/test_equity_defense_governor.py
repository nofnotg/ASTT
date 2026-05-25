from __future__ import annotations

from portfolio.equity_defense_governor import POLICIES, EquityDefenseGovernor


def test_rolling_edge_throttle_reduces_risk_after_weak_recent_trades():
    governor = EquityDefenseGovernor(POLICIES["ROLLING_EDGE_THROTTLE"], 500000)
    for idx in range(20):
        governor.record_result({"market": "KRW-BTC", "entry_time": f"2025-01-{idx + 1:02d}"}, -1000)

    decision = governor.evaluate({"market": "KRW-BTC", "entry_time": "2025-02-01"})

    assert decision["defense_action"] == "ENTER"
    assert decision["risk_multiplier_after_defense"] == 0.35
    assert "ROLLING_EDGE_THROTTLE" in decision["defense_reasons"]


def test_drawdown_throttle_reduces_risk_after_equity_peak_damage():
    governor = EquityDefenseGovernor(POLICIES["DRAWDOWN_THROTTLE"], 500000)
    governor.record_result({"market": "KRW-BTC", "entry_time": "2025-01-01"}, 100000)
    governor.record_result({"market": "KRW-BTC", "entry_time": "2025-01-02"}, -70000)

    decision = governor.evaluate({"market": "KRW-BTC", "entry_time": "2025-01-03"})

    assert decision["defense_action"] == "ENTER"
    assert decision["risk_multiplier_after_defense"] == 0.5
    assert "DRAWDOWN_THROTTLE_10" in decision["defense_reasons"]


def test_baseline_policy_never_changes_paper_risk():
    governor = EquityDefenseGovernor(POLICIES["BASELINE"], 500000)
    for idx in range(30):
        governor.record_result({"market": "KRW-BTC", "entry_time": f"2025-01-{idx + 1:02d}"}, -1000)

    decision = governor.evaluate({"market": "KRW-BTC", "entry_time": "2025-02-01"})

    assert decision["defense_action"] == "ENTER"
    assert decision["risk_multiplier_after_defense"] == 1.0
    assert decision["defense_reasons"] == []
