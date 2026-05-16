from execution.risk_gate_v5 import evaluate_risk_gate_v5


def test_risk_gate_veto_and_pass():
    assert evaluate_risk_gate_v5({"regime": {"regime": "BTC_SHOCK", "long_allowed": False}, "risk_reward": 2, "target_space_pct": 1})["veto"]
    assert evaluate_risk_gate_v5({"regime": {"regime": "RISK_ON", "long_allowed": True}, "risk_reward": 0.8, "target_space_pct": 1})["veto"]
    assert evaluate_risk_gate_v5({"regime": {"regime": "RISK_ON", "long_allowed": True}, "risk_reward": 1.5, "target_space_pct": 1})["risk_decision"] == "PASS"
