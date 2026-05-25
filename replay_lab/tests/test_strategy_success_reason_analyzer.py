from __future__ import annotations

from analysis.strategy_success_reason_analyzer import analyze_strategy_success


def test_strategy_success_reason_analyzer_lists_surviving_setups():
    result = analyze_strategy_success("S", [{"setup_type": "FVG", "market": "KRW-BTC", "pnl_krw": 10}])
    assert result["surviving_setups"] == ["FVG"]
