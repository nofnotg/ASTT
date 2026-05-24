from execution.redesigned_source_forward_runner import run_redesigned_source_forward_test_v559


def test_forward_runner_summary_shape():
    result = run_redesigned_source_forward_test_v559(duration_minutes=1, top_markets=1)
    assert result["real_order_enabled"] is False
    assert result["research_mode"] is True
    assert "candidate_count" in result
