from features.fractal_mtf_context import compute_fractal_mtf_context


def test_fractal_states():
    full = compute_fractal_mtf_context({"weekly_power_score": 80}, {"daily_structure_score": 70}, {"h4_flow_score": 65}, {"score": 80}, {"score": 80}, {"score": 80})
    assert full["fractal_state"] == "FULL_ALIGNMENT"
    conflict = compute_fractal_mtf_context({"weekly_power_score": 20}, {"daily_structure_score": 30}, {"h4_flow_score": 30}, {"score": 80}, {"score": 80}, {"score": 80})
    assert conflict["recommended_mode"] in {"PAPER_ONLY", "NO_TRADE"}
