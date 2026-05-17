from __future__ import annotations

from execution.allocation_policy_v53 import decide_allocation_v53


def test_allocation_policy_v53_grade_and_risk_off():
    strong = decide_allocation_v53(500000, "A_PLUS", "A_PLUS", "FULL_ALIGNMENT", "ALT_RISK_ON")
    veto = decide_allocation_v53(500000, "A_PLUS", "A_PLUS", "FULL_ALIGNMENT", "RISK_OFF")
    cut = decide_allocation_v53(500000, "A", "A", "CONFLICT", "BTC_LED", consecutive_loss=2)
    assert strong["allocation_pct"] >= 0.8
    assert veto["allocation_pct"] == 0
    assert cut["allocation_pct"] < 0.3
