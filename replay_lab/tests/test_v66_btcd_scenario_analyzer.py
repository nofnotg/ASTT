from __future__ import annotations

import pandas as pd

from analysis.v66_btcd_scenario_analyzer import analyze_v66_btcd_scenarios


def test_v66_btcd_scenario_analyzer_runs_without_future_data(tmp_path):
    daily = tmp_path / "1d"
    daily.mkdir()
    times = pd.date_range("2024-01-01", periods=40, freq="D")
    pd.DataFrame({"market": "KRW-BTC", "time": times, "trade_price": [1000.0 for _ in times]}).to_parquet(daily / "KRW-BTC.parquet")
    pd.DataFrame({"market": "KRW-ALT", "time": times, "trade_price": [1000.0 for _ in times]}).to_parquet(daily / "KRW-ALT.parquet")
    journal = [
        {
            "trade_id": "t1",
            "entry_time": "2024-01-10 10:00:00",
            "exit_time": "2024-01-10 12:00:00",
            "feature_cutoff_time": "2024-01-10 09:00:00",
            "market": "KRW-ALT",
            "plan": "PLAN_A_ICT_FAT_TAIL",
            "strategy": "ICT_FVG_OB_SWEEP",
            "setup_type": "FVG_OB_OVERLAP",
            "entry_price": 100.0,
            "exit_price": 110.0,
            "stop_price": 95.0,
        }
    ]

    result = analyze_v66_btcd_scenarios(journal, 500000, tmp_path)

    assert len(result["scenarios"]) == 9
    assert result["audit"]["fail"] == 0

