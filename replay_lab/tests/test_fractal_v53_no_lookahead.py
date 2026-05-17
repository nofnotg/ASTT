from __future__ import annotations

import pandas as pd

from features.feature_snapshot_cache import get_or_build_feature_snapshot
from features.zone_reaction_labeler import label_zone_reaction


def test_v53_decision_snapshot_excludes_future_and_reaction_is_post_entry(tmp_path):
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01 00:00", periods=5, freq="min"), "close": [100, 101, 102, 103, 104], "high": [101, 102, 103, 104, 105], "low": [99, 100, 101, 102, 103]})
    snap = get_or_build_feature_snapshot("KRW-TEST", "2026-01-01 00:02", {"1m": frame}, {"timeframe": "1m"}, str(tmp_path))
    assert snap["snapshot"]["timeframes"]["1m"]["latest_close"] == 102
    reaction = label_zone_reaction(frame, {"zone_low": 99, "zone_high": 100}, "2026-01-01 00:02", "DEMAND")
    assert reaction["horizon_bars"] == 2
    assert reaction["touch_time"].startswith("2026-01-01T00:02")
