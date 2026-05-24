from winner_mining.source_discriminative_power import FEATURES


def test_discriminative_feature_list_contains_core_fields():
    names = [name for name, _ in FEATURES]
    assert "buy_trade_ratio_10s" in names
    assert "spread_pct" in names
