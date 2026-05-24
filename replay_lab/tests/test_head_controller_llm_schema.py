import pytest

from head_controller.llm_json_schema import validate_and_sanitize_llm_output


def test_llm_schema_forces_inactive():
    out = validate_and_sanitize_llm_output({"live_readiness_opinion": "LIVE_NOT_ALLOWED", "primary_problem": "X", "config_proposals": [{"proposal_id": "p", "active": True, "human_approved": True}]})
    assert out["config_proposals"][0]["active"] is False
    assert out["config_proposals"][0]["human_approved"] is False


def test_llm_schema_rejects_live_ready():
    with pytest.raises(ValueError):
        validate_and_sanitize_llm_output({"live_readiness_opinion": "LIVE_READY"})
