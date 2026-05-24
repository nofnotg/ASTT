import json

from scenario_lab import scenario_factory


def test_scenario_factory_v5r3_reuses_setup_and_fake_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scenario_factory, "REPLAY_STORE_DIR", tmp_path / "replay_store")
    setup_dir = tmp_path / "replay_store" / "setup_candidates"
    fake_dir = tmp_path / "replay_store" / "fake_signal"
    setup_dir.mkdir(parents=True)
    fake_dir.mkdir(parents=True)
    (setup_dir / "latest_setup_candidate_summary.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "c1",
                        "clip_id": "clip1",
                        "event_id": "event1",
                        "market": "KRW-ETH",
                        "event_type": "VOLUME_SPIKE",
                        "setup_type": "VWAP_RECLAIM_WITH_VOLUME",
                        "setup_score": 70,
                        "setup_grade": "A",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (fake_dir / "fake_signal_decomposition.json").write_text(
        json.dumps({"rows": [{"clip_id": "clip2", "event_id": "event2", "market": "KRW-XRP", "fake_subtype": "RANK_SURGE_FAKE"}]}),
        encoding="utf-8",
    )

    result = scenario_factory.build_scenarios_v5r3()

    assert result["scenario_count"] == 2
    assert "VOLUME_SURGE" in result["scenario_counts"]
    assert result["real_order_enabled"] is False
