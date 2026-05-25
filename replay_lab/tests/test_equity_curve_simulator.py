from __future__ import annotations

from portfolio.equity_curve_simulator import simulate_equity_curve


def test_equity_curve_simulator_builds_safe_journal():
    result = simulate_equity_curve(500000, True)
    assert result["trade_count"] > 0
    assert result["real_order_enabled"] is False
    assert result["journal"][0]["equity_before"] == 500000
