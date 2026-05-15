import pandas as pd

from features.support_resistance import body_zone_context, moving_average_context


def test_body_zone_and_ma_context():
    frame = pd.DataFrame(
        {
            "time": range(80),
            "open": [100 + i * 0.02 for i in range(80)],
            "high": [101 + i * 0.02 for i in range(80)],
            "low": [99 + i * 0.02 for i in range(80)],
            "close": [100.2 + i * 0.02 for i in range(80)],
            "volume": [100] * 70 + [1000] * 10,
        }
    )
    ma = moving_average_context(frame)
    zone = body_zone_context(frame, price=float(frame.iloc[-1]["close"]))
    assert 0 <= ma["ma_context_score"] <= 100
    assert "nearest_support_zone" in zone
    assert "target_space_pct" in zone
