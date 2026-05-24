from execution.source_candidate_gate_v559 import evaluate_source_candidate_gate_v559


def test_source_candidate_gate_enter_only_for_safe_candidate():
    candidate = {"real_order_enabled": False, "expected_target_pct": 0.35}
    assert evaluate_source_candidate_gate_v559(candidate)["decision"] == "ENTER"
    assert evaluate_source_candidate_gate_v559(None)["decision"] == "WAIT"
