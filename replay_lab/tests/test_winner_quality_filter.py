from winner_mining.winner_effective_move import calculate_effective_move
from winner_mining.tick_noise_filter import evaluate_tick_noise


def test_quality_filter_components_generate_reject_reasons():
    effective = calculate_effective_move(0.25, 0.2, 0.2)
    tick = evaluate_tick_noise(149, 150, effective["effective_return_pct"])
    reject_reasons = []
    if tick["is_tick_noise"]:
        reject_reasons.append("TICK_NOISE")
    if effective["effective_return_pct"] < 0.20:
        reject_reasons.append("EFFECTIVE_RETURN_TOO_LOW")
    assert "TICK_NOISE" in reject_reasons
