from __future__ import annotations

import pandas as pd

from features.zone_reaction_labeler import label_zone_reaction


def _frame(highs, lows, closes):
    return pd.DataFrame({"time": pd.date_range("2026-01-01 00:01", periods=len(highs), freq="min"), "open": closes, "high": highs, "low": lows, "close": closes, "volume": 1})


def test_zone_reaction_bounce_success():
    frame = _frame([101, 103], [99, 100], [102, 103])
    label = label_zone_reaction(frame, {"zone_low": 99, "zone_high": 100}, "2026-01-01 00:00", "DEMAND")
    assert label["reaction_label"] == "BOUNCE_SUCCESS"
    assert label["hit_1r"] is True


def test_zone_reaction_breakdown_fail_and_no_reaction():
    fail = label_zone_reaction(_frame([100, 100], [98, 97], [98, 97]), {"zone_low": 99, "zone_high": 100}, "2026-01-01 00:00", "DEMAND")
    quiet = label_zone_reaction(_frame([100.2, 100.1], [99.8, 99.7], [100, 99.9]), {"zone_low": 99, "zone_high": 100}, "2026-01-01 00:00", "DEMAND")
    assert fail["reaction_label"] == "BREAKDOWN_FAIL"
    assert quiet["reaction_label"] in {"NO_REACTION", "CHOP"}
