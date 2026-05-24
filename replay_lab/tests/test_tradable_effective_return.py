from tradable_winner.tradable_effective_return import calculate_tradable_effective_return


def test_tradable_effective_return_subtracts_costs():
    result = calculate_tradable_effective_return(1.0, 0.1, 0.1, 0.05, 0.05)
    assert round(result["effective_return_pct"], 4) == 0.7
    assert result["reward_to_cost_ratio"] > 3
