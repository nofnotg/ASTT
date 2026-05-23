from research_external.external_indicator_taxonomy import build_indicator_taxonomy, classify_indicator


def test_indicator_taxonomy_classifies_groups_and_roles():
    taxonomy = build_indicator_taxonomy()
    groups = {row["group"] for row in taxonomy}

    assert "Trend" in groups
    assert "Microstructure" in groups
    assert classify_indicator("RSI")["group"] == "Momentum"
    assert classify_indicator("spread")["astt_role"] == "risk"
