from __future__ import annotations

from pathlib import Path

import pandas as pd

from btcd.btcdom_index_feature_builder import BTCDOMIndexFeatureStore


def test_btcdom_index_feature_builder_uses_last_closed_candle(tmp_path: Path):
    for tf in ("1h", "4h", "1d"):
        frame = pd.DataFrame(
            [
                {"timestamp": "2023-05-28T00:00:00Z", "open": 1, "high": 1, "low": 1, "close": 1600, "volume": 1},
                {"timestamp": "2023-05-29T00:00:00Z", "open": 1, "high": 1, "low": 1, "close": 1610, "volume": 1},
            ]
        )
        frame.to_csv(tmp_path / f"btcdom_index_{tf}_normalized.csv", index=False)
    store = BTCDOMIndexFeatureStore(tmp_path)
    feature = store.feature_for("2023-05-28T12:00:00Z")
    assert feature["btcdom_feature_time_1d"] == "2023-05-28T00:00:00+00:00"
    assert feature["btcdom_index_close_1d"] == 1600
    assert feature["lookahead_check"] == "PASS"
