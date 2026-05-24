from replay_lab.research.sizing_mode_comparison_v557 import compare_sizing_modes_v557


def test_sizing_mode_comparison_contains_required_modes():
    result = compare_sizing_modes_v557()
    modes = {row["mode"] for row in result["sizing_mode_results"]}
    assert {"FIXED_10K", "FIXED_100K", "FULL_SEED_SINGLE", "FULL_SEED_LADDER"} <= modes
