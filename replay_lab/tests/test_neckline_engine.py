import pandas as pd

from daddy_strategy.neckline_engine import detect_neckline


def test_neckline_engine_returns_level():
    frame = pd.DataFrame({"high": [100 + i % 3 for i in range(40)], "close": [101 for _ in range(40)]})
    assert detect_neckline(frame)["neckline"] > 0
