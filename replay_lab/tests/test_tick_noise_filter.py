from winner_mining.tick_noise_filter import evaluate_tick_noise


def test_tick_noise_rejects_one_tick_low_price_move():
    result = evaluate_tick_noise(149, 150, 0.2)
    assert result["raw_move_ticks"] == 1
    assert result["is_tick_noise"] is True
