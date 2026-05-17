from __future__ import annotations

import pandas as pd

from features.dominance_loader import align_dominance_to_replay_time, load_btc_dominance_data


def test_dominance_loader_csv_alias_and_align(tmp_path):
    path = tmp_path / "dom.csv"
    pd.DataFrame({"datetime": ["2026-01-01 00:00", "2026-01-01 01:00"], "dominance": [51.0, 50.5]}).to_csv(path, index=False)
    frame = load_btc_dominance_data(str(path))
    aligned = align_dominance_to_replay_time(frame, "2026-01-01 01:20", tolerance_minutes=60)
    assert list(frame.columns) == ["time", "btc_dominance"]
    assert aligned["dominance_available"] is True
    assert aligned["dominance_value"] == 50.5


def test_dominance_loader_stale_warning():
    frame = pd.DataFrame({"time": pd.to_datetime(["2026-01-01 00:00"]), "btc_dominance": [50]})
    aligned = align_dominance_to_replay_time(frame, "2026-01-01 03:00", tolerance_minutes=30)
    assert aligned["stale"] is True
    assert "stale_dominance" in aligned["warnings"]
