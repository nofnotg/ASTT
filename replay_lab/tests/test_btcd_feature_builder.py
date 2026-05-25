from __future__ import annotations

import pandas as pd

from btcd.btcd_feature_builder import BTCDFeatureStore


def test_btcd_feature_builder_uses_past_flow_only(tmp_path):
    daily = tmp_path / "1d"
    daily.mkdir()
    times = pd.date_range("2024-01-01", periods=10, freq="D")
    pd.DataFrame({"market": "KRW-BTC", "time": times, "trade_price": [100.0 + i for i in range(10)]}).to_parquet(daily / "KRW-BTC.parquet")
    pd.DataFrame({"market": "KRW-ALT", "time": times, "trade_price": [200.0 for _ in range(10)]}).to_parquet(daily / "KRW-ALT.parquet")

    store = BTCDFeatureStore(tmp_path, tmp_path, tmp_path / "missing.csv")
    feature = store.feature_for("2024-01-05 12:00:00")

    assert feature.lookahead_check == "PASS"
    assert feature.upbit_flow.timestamp.startswith("2024-01-05")

