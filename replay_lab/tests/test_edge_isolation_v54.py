from __future__ import annotations

import json

import pandas as pd

from replay_lab.replay.edge_isolation_v54 import run_edge_isolation_v54


def test_edge_isolation_v54_fixed_order_no_allocation(tmp_path):
    store = tmp_path / "replay_store"
    v53 = store / "experiments" / "exp_20260101_000000_fractal_v53"
    v53.mkdir(parents=True)
    pd.DataFrame([{"date_kst": "2026-01-01", "market": "KRW-BTC", "signal_time_kst": "2026-01-01T00:00:00", "entry_time_kst": "2026-01-01T00:01:00", "entry_price": 100.0, "zone_stop": 99.0, "target_1": 101.0, "daily_structure_score": 70, "h4_flow_score": 65, "v5_score": 80, "btc_regime": "ALT_RISK_ON"}]).to_parquet(v53 / "paper_trades.parquet")
    (v53 / "config.json").write_text(json.dumps({"start_date": "2026-01-01", "end_date": "2026-01-01", "top_markets": 1}), encoding="utf-8")
    data = store / "normalized" / "candles_1m"
    data.mkdir(parents=True)
    pd.DataFrame({"candle_time_kst": pd.date_range("2026-01-01 00:00", periods=5, freq="min"), "open": [100] * 5, "high": [100, 100, 101.5, 101.5, 101.5], "low": [99.8] * 5, "close": [100, 100.5, 101, 101, 101], "volume": [1] * 5, "trade_price": [1] * 5}).to_parquet(data / "KRW-BTC.parquet")
    exp = run_edge_isolation_v54(__import__("datetime").date(2026, 1, 1), __import__("datetime").date(2026, 1, 1), top_markets=1, fixed_order_krw=10000, store_dir=store)
    metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["strategy_results"]
    trades = pd.read_parquet(exp / "edge_trades.parquet")
    assert "allocation_pct" not in trades.columns
    assert float(trades.iloc[0]["order_pnl_krw"]) != 0
