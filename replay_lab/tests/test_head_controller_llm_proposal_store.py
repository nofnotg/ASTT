import json

from head_controller.llm_proposal_store import store_llm_proposal


def test_head_controller_llm_proposal_store_defaults_safe():
    path = store_llm_proposal({"proposal_id": "test_prop"}, "off", "PASS")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["active"] is False
    assert data["human_approved"] is False
    assert data["applied"] is False
