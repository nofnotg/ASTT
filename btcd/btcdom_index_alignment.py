from __future__ import annotations

from typing import Any

import pandas as pd


def btcdom_lookahead_pass(feature: dict[str, Any], decision_time: str) -> bool:
    if feature.get("lookahead_check") != "PASS":
        return False
    for key in ("btcdom_feature_time_1h", "btcdom_feature_time_4h", "btcdom_feature_time_1d"):
        value = feature.get(key)
        if value and _after(str(value), decision_time):
            return False
    return True


def _after(left: str, right: str) -> bool:
    try:
        l = pd.Timestamp(left)
        r = pd.Timestamp(right)
        if l.tzinfo is None:
            l = l.tz_localize("UTC")
        else:
            l = l.tz_convert("UTC")
        if r.tzinfo is None:
            r = r.tz_localize("UTC")
        else:
            r = r.tz_convert("UTC")
        return l > r
    except Exception:
        return True
