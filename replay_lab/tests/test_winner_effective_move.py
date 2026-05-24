from winner_mining.winner_effective_move import calculate_effective_move


def test_effective_move_subtracts_fee_spread_slippage():
    result = calculate_effective_move(0.6, entry_spread_pct=0.1, exit_spread_pct=0.1, slippage_pct=0.05, fee_pct=0.05)
    assert round(result["effective_return_pct"], 4) == 0.4
    assert result["reward_to_cost_ratio"] > 2
