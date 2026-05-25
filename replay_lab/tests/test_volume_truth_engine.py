import pandas as pd

from daddy_strategy.volume_truth_engine import analyze_volume_truth


def test_volume_truth_engine_detects_breakout_with_volume():
    frame = pd.DataFrame([{"open": 100, "high": 101+i*0.1, "low": 99, "close": 100+i*0.1, "volume": 10} for i in range(19)] + [{"open": 102, "high": 105, "low": 101, "close": 106, "volume": 30}])
    assert analyze_volume_truth(frame)["volume_signal"] == "BREAKOUT_WITH_VOLUME"
