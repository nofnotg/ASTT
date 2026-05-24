from replay_lab.research.head_controller_openai_live_check_v5562 import validate_head_controller_proposals_v5562


def test_proposal_validation_stores_inactive_records():
    result = validate_head_controller_proposals_v5562("docs/reports")
    assert result["active"] is False
    assert result["human_approved"] is False
    assert result["applied"] is False
