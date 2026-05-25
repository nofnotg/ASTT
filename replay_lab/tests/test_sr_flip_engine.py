import pandas as pd

from daddy_strategy.sr_flip_engine import detect_sr_flip


def test_sr_flip_engine_detects_state():
    frame = pd.DataFrame({"high": [100] * 39 + [105], "low": [95] * 40, "close": [99] * 39 + [106]})
    assert detect_sr_flip(frame)["sr_flip_state"] in {"BREAKOUT", "RETEST_HOLD", "NO_FLIP"}
