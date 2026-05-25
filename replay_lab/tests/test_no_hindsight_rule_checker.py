from __future__ import annotations

from validation.no_hindsight_rule_checker import check_no_hindsight_rules


def test_no_hindsight_rule_checker_rejects_known_drawdown_marker():
    result = check_no_hindsight_rules({"causal_policy_notes": "turn on at 2025-05-13"})

    assert result["status"] == "FAIL"
