from replay_lab.research.head_controller_openai_live_check_v5562 import run_head_controller_unsafe_prompt_test_v5562


def test_openai_live_unsafe_prompt_contract_blocks_live_controls():
    result = run_head_controller_unsafe_prompt_test_v5562("openai")
    assert result["unsafe_proposal_detected"] is True
    assert result["llm_output_rejected"] is True
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
    assert result["active"] is False
    assert result["human_approved"] is False
