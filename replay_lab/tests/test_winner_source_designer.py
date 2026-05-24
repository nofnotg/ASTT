from winner_mining.winner_source_designer import design_winner_sources


def test_winner_source_designer_keeps_research_mode():
    sources = design_winner_sources([{"pattern_id": "VOLUME_RANGE_BREAKOUT", "support_count": 1}])
    assert sources[0]["research_mode"] is True
    assert sources[0]["real_order_enabled"] is False
    assert sources[0]["auto_apply_allowed"] is False
