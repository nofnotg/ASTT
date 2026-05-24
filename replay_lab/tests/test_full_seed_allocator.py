from capital.capital_policy import default_capital_policy
from capital.full_seed_allocator import allocate_full_seed


def test_full_seed_allocator_never_enables_real_orders():
    result = allocate_full_seed({"entry_decision": "ENTER", "micro_strength_score": 85}, default_capital_policy())
    assert result["signal_grade"] == "S"
    assert result["real_order_enabled"] is False
    assert result["research_mode"] is True
