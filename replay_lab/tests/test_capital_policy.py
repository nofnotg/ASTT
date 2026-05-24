import pytest

from capital.capital_policy import default_capital_policy, validate_capital_policy


def test_capital_policy_defaults_are_research_only():
    policy = default_capital_policy()
    assert policy["initial_cash_krw"] == 500000
    assert policy["real_order_enabled"] is False
    assert policy["research_mode"] is True


def test_capital_policy_rejects_real_order_enabled():
    with pytest.raises(ValueError):
        validate_capital_policy({"real_order_enabled": True})
