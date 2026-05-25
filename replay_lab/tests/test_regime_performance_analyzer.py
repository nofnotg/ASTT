from __future__ import annotations

from analysis.regime_performance_analyzer import analyze_regime_performance, classify_trade_regime


def test_regime_performance_analyzer_groups_by_setup():
    trade = {"trade_id": "t", "setup_type": "FVG_LIQUIDITY_SWEEP", "pnl_krw": 100, "return_pct": 1.0}
    assert classify_trade_regime(trade) == "ALT_ROTATION"
    rows = analyze_regime_performance("S", [trade])
    assert rows[0]["decision"] == "KEEP_WITH_REGIME_FILTER"
