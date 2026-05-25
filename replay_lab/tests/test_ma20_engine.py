import pandas as pd

from daddy_strategy.ma20_engine import analyze_ma20


def test_ma20_engine_detects_above_ma20():
    frame = pd.DataFrame({"close": list(range(1, 25))})
    assert analyze_ma20(frame)["ma20_state"] in {"ABOVE_MA20", "MA20_RECLAIM"}
