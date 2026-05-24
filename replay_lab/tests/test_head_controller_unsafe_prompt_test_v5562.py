from head_controller.llm_json_schema import validate_and_sanitize_llm_output


def test_unsafe_prompt_sanitizer_forces_proposal_inactive():
    result = validate_and_sanitize_llm_output({
        "summary": "probe",
        "live_readiness_opinion": "LIVE_NOT_ALLOWED",
        "primary_problem": "probe",
        "root_cause_hypotheses": [],
        "next_experiments": ["auto apply"],
        "risk_flags": [],
        "config_proposals": [{"proposal_id": "p", "active": True, "human_approved": True}],
        "auto_apply_allowed": True,
        "live_order_allowed": True,
    })
    assert result["auto_apply_allowed"] is False
    assert result["live_order_allowed"] is False
    assert result["config_proposals"][0]["active"] is False
    assert result["config_proposals"][0]["human_approved"] is False
    assert "LLM_UNSAFE_PROPOSAL_REJECTED" in result["risk_flags"]
