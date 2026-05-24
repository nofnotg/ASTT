from execution.redesigned_source_paper_executor import execute_redesigned_source_paper


def test_paper_executor_never_creates_trade_for_wait():
    result = execute_redesigned_source_paper({}, "WAIT")
    assert result["paper_trade_created"] is False
    assert result["included_in_pnl"] is False
