from execution.tradable_candidate_gate_v5510 import evaluate_tradable_candidate_gate_v5510


def test_tradable_gate_rejects_cost_spread_depth():
    base = {"real_order_enabled": False, "tradable_prefilter_pass": True, "effective_return_pct": 0.5, "spread_pct": 0.1, "depth_3_level_krw": 2_000_000}
    assert evaluate_tradable_candidate_gate_v5510(base)["decision"] == "ENTER"
    assert evaluate_tradable_candidate_gate_v5510({**base, "effective_return_pct": 0})["decision"] == "WAIT"
    assert evaluate_tradable_candidate_gate_v5510({**base, "spread_pct": 0.5})["decision"] == "WAIT"
    assert evaluate_tradable_candidate_gate_v5510({**base, "depth_3_level_krw": 10})["decision"] == "WAIT"
