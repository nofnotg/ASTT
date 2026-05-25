from __future__ import annotations

from analysis.setup_context_improvement_analyzer import analyze_setup_context_improvement
from portfolio.trade_journal_builder import build_trade_journal


def test_setup_context_improvement_analyzer_outputs_decisions():
    rows = analyze_setup_context_improvement(build_trade_journal()["journal"])
    assert rows
    assert rows[0]["decision"] in {"STRENGTHEN", "KEEP"}
