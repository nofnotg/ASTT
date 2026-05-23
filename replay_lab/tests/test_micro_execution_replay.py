import json

import pandas as pd

from replay_lab.replay.micro_execution_replay import run_micro_execution_replay


def test_micro_execution_replay_uses_post_entry_seconds_and_marks_unavailable(tmp_path):
    edge = tmp_path / "experiments" / "exp_20260501_000000_edge_isolation_v54"
    edge.mkdir(parents=True)
    pd.DataFrame([
        {
            "date_kst": "2026-05-01",
            "market": "KRW-BTC",
            "strategy_id": "MTF_ONLY",
            "exit_model": "FIXED_RR_1_5",
            "entry_time_kst": "2026-05-01T09:00:00",
            "entry_price": 100.0,
            "target_price": 100.6,
            "stop_price": 99.6,
        }
    ]).to_parquet(edge / "edge_trades.parquet", index=False)
    (edge / "config.json").write_text(json.dumps({"seed": "test"}), encoding="utf-8")
    candles_root = tmp_path / "normalized" / "candles_1m"
    candles_root.mkdir(parents=True)
    pd.DataFrame([
        {"time": "2026-05-01T09:00:00", "open": 100, "high": 100.8, "low": 99.9, "close": 100.7, "volume": 60, "trade_price": 6000},
        {"time": "2026-05-01T09:01:00", "open": 100.7, "high": 100.9, "low": 100.2, "close": 100.3, "volume": 60, "trade_price": 6000},
    ]).to_parquet(candles_root / "KRW-BTC.parquet", index=False)

    exp = run_micro_execution_replay("2026-05-01", "2026-05-01", top_markets=1, store_dir=tmp_path)
    metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8"))

    assert metrics["entry_count"] == 1
    assert metrics["data_quality_summary"]["UNAVAILABLE"] == 1
    assert metrics["live_readiness"] == "LIVE_NOT_ALLOWED"
