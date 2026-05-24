from winner_mining.non_winner_sampler import SAMPLE_TYPES


def test_non_winner_sampler_types_exist():
    assert "COMPRESSION_NO_BREAKOUT" in SAMPLE_TYPES
    assert "ORDERFLOW_FAKE_SURGE" in SAMPLE_TYPES
    assert "RANDOM_CONTROL" in SAMPLE_TYPES
