import pandas as pd

from features.ichimoku_context import compute_ichimoku_context


def test_ichimoku_cloud_state():
    frame = pd.DataFrame({"open": range(100, 170), "high": range(101, 171), "low": range(99, 169), "close": range(100, 170), "volume": [100] * 70})
    result = compute_ichimoku_context(frame)
    assert result["cloud_state"] in {"ABOVE_CLOUD", "INSIDE_CLOUD", "BELOW_CLOUD"}
    assert "long_allowed" in result
