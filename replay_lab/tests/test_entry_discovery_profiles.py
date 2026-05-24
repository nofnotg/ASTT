from features.entry_discovery_profiles import get_entry_discovery_profile


def test_entry_discovery_profile_marks_research_only():
    assert get_entry_discovery_profile("ENTRY_DISCOVERY")["research_only"] is True
    assert get_entry_discovery_profile("STRICT")["research_only"] is False
