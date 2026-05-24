from timing_lab.fake_signal_decomposer import _decompose


def test_fake_signal_decomposer_assigns_subtype_and_action():
    label = {"clip_id": "c", "event_id": "e_VOLUME_SPIKE", "market": "KRW-BTC", "reason": [], "max_mfe_pct": 0}
    row = _decompose(label, {"event_type": "VOLUME_SPIKE"}, [], [])
    assert row["fake_subtype"] == "VOLUME_ONLY_FAKE"
    assert row["suggested_action"]
