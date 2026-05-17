from __future__ import annotations

import pandas as pd

from features.feature_snapshot_cache import get_or_build_feature_snapshot


def test_feature_snapshot_cache_hit_miss_and_no_future(tmp_path):
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01 00:00", periods=4, freq="min"), "close": [1, 2, 3, 4]})
    as_of = pd.Timestamp("2026-01-01 00:01")
    first = get_or_build_feature_snapshot("KRW-TEST", as_of, {"1m": frame}, {"a": 1}, str(tmp_path))
    second = get_or_build_feature_snapshot("KRW-TEST", as_of, {"1m": frame}, {"a": 1}, str(tmp_path))
    changed = get_or_build_feature_snapshot("KRW-TEST", as_of, {"1m": frame}, {"a": 2}, str(tmp_path))
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert changed["cache_hit"] is False
    assert second["snapshot"]["timeframes"]["1m"]["row_count"] == 2
    assert second["snapshot"]["timeframes"]["1m"]["future_rows_included"] is False
