from execution.tradable_source_forward_runner import run_tradable_source_forward_validation_v5510


def test_tradable_source_forward_runner_paper_only():
    result = run_tradable_source_forward_validation_v5510("RECORDED_VALIDATION", 500000, True, 0)
    assert result["real_order_enabled"] is False
    assert result["research_mode"] is True
    assert "candidate_count" in result
