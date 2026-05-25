from __future__ import annotations

import pandas as pd

from btcd.upbit_btc_flow_dominance import build_upbit_btc_flow_dominance


def test_upbit_btc_flow_dominance_calculates_proxy(tmp_path):
    daily = tmp_path / "1d"
    daily.mkdir()
    times = pd.to_datetime(["2024-01-01", "2024-01-02"])
    pd.DataFrame({"market": "KRW-BTC", "time": times, "trade_price": [100.0, 300.0]}).to_parquet(daily / "KRW-BTC.parquet")
    pd.DataFrame({"market": "KRW-ALT", "time": times, "trade_price": [100.0, 100.0]}).to_parquet(daily / "KRW-ALT.parquet")

    frame, quality = build_upbit_btc_flow_dominance(tmp_path, tmp_path)

    assert quality["available"] is True
    assert round(float(frame.iloc[0]["upbit_btc_flow_dominance_pct"]), 2) == 50.0
    assert round(float(frame.iloc[1]["upbit_btc_flow_dominance_pct"]), 2) == 75.0

