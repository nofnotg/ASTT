import pandas as pd

from ict_strategy.liquidity_sweep_detector import detect_liquidity_sweeps


def test_liquidity_sweep_detector_detects_reclaim():
    rows = [{"time": i, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1} for i in range(20)]
    rows.append({"time": 21, "open": 100, "high": 102, "low": 98, "close": 100.5, "volume": 2})
    assert any(row["sweep_type"] == "BULLISH_LIQUIDITY_SWEEP" for row in detect_liquidity_sweeps(pd.DataFrame(rows)))
