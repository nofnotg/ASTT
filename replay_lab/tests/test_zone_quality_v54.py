from __future__ import annotations

import pandas as pd

from features.zone_quality_v54 import compute_zone_quality_v54


def test_zone_quality_overlap_width_grade():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=5, freq="min"), "open": [100] * 5, "high": [101] * 5, "low": [99] * 5, "close": [100] * 5, "volume": [10, 20, 30, 20, 10]})
    result = compute_zone_quality_v54({"zone_low": 99.5, "zone_high": 100.5}, frame, [{"zone_low": 99, "zone_high": 101}], "2026-01-01 00:04")
    assert result["htf_overlap"] is True
    assert result["zone_width_ok"] is True
    assert result["quality_grade"] in {"A", "B", "C", "REJECT"}
