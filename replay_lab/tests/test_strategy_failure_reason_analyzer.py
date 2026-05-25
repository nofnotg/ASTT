from __future__ import annotations

from analysis.strategy_failure_reason_analyzer import analyze_strategy_failure


def test_strategy_failure_reason_analyzer_marks_daddy_issue():
    result = analyze_strategy_failure("DADDY_VOLUME_NECKLINE", [{"setup_type": "SR", "pnl_krw": -1}])
    assert "volume_location_signal_not_sufficient_alone" in result["avoid_conditions"]
