import pandas as pd

from market_data.ohlcv_store import OHLCVStore
from mtf.mtf_context_builder import build_v6_mtf_context


def test_mtf_context_builder_outputs_scores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = OHLCVStore(tmp_path / "v6")
    frame = pd.DataFrame([{"time": f"2026-01-{(i%28)+1:02d}", "open": 100+i, "high": 101+i, "low": 99+i, "close": 100+i, "volume": 10, "trade_price": 1000} for i in range(40)])
    for tf in ["1w", "1d", "4h", "1h"]:
        store.save(tf, "KRW-BTC", frame)
    result = build_v6_mtf_context("KRW-BTC", store)
    assert result["market_count"] == 1
    assert "mtf_score" in result["contexts"][0]
