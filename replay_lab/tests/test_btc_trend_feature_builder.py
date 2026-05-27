from __future__ import annotations

import pandas as pd

from btcd.btc_trend_feature_builder import BTCTrendFeatureStore


def test_btc_trend_feature_builder_reads_btc_daily(tmp_path):
    daily = tmp_path / "1d"
    daily.mkdir()
    pd.DataFrame({"time": pd.date_range("2024-01-01", periods=40), "trade_price": range(100, 140)}).to_parquet(daily / "KRW-BTC.parquet")
    store = BTCTrendFeatureStore(tmp_path, tmp_path)
    feature = store.feature_for("2024-02-10")
    assert feature["btc_structure"] in {"UPTREND", "RECOVERY", "RANGE"}
    assert feature["lookahead_check"] == "PASS"
