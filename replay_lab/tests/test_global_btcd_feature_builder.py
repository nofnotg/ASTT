from __future__ import annotations

import pandas as pd

from btcd.global_btcd_feature_builder import GlobalBTCDHistoryFeatureStore


def test_global_btcd_feature_uses_only_prior_rows(tmp_path):
    path = tmp_path / "hist.csv"
    pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=10), "btc_dominance_pct": range(40, 50), "source": ["csv"] * 10}).to_csv(path, index=False)
    store = GlobalBTCDHistoryFeatureStore(path)
    feature = store.feature_for("2024-01-05 12:00:00")
    assert feature["timestamp"].startswith("2024-01-05")
    assert feature["lookahead_check"] == "PASS"
