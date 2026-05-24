from execution.full_seed_paper_runner import run_full_seed_paper_session_v557


def test_full_seed_paper_runner_enter_zero_is_not_pnl_evaluable():
    result = run_full_seed_paper_session_v557(duration_minutes=0)
    assert result["real_order_enabled"] is False
    assert result["research_mode"] is True
    if result["enter_count"] == 0:
        assert result["pnl_evaluable"] is False
        assert result["profit_factor"] is None
