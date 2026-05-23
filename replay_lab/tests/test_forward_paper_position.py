from execution.forward_paper_position import ForwardPaperPosition


def test_forward_paper_position_close_with_cost_fields():
    pos = ForwardPaperPosition("p1", "KRW-BTC", "2026-05-01T09:00:00", 100, 10000, 101, 99)
    result = pos.close(100.5, "TAKE_PROFIT")

    assert result["status"] == "CLOSED"
    assert result["pnl_pct"] > 0
    assert "realistic_1_pnl_krw" in result
