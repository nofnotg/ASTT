from features.micro_entry_gate_profiles import get_gate_profile, list_gate_profiles


def test_gate_profiles_exist_and_exploratory_is_research_only():
    profiles = list_gate_profiles()

    assert {"STRICT", "BALANCED", "EXPLORATORY"} <= set(profiles)
    assert get_gate_profile("EXPLORATORY")["research_only"] is True
    assert get_gate_profile("STRICT")["research_only"] is False
