from winner_mining.winner_pattern_miner import PATTERN_IDS


def test_winner_pattern_miner_has_required_patterns():
    assert "VOLUME_RANGE_BREAKOUT" in PATTERN_IDS
    assert "ORDERFLOW_SURGE" in PATTERN_IDS
