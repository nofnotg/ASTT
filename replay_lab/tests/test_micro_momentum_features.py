import pandas as pd

from features.micro_momentum_features import compute_micro_momentum_after_entry


def test_micro_momentum_after_entry_detects_failure():
    frame = pd.DataFrame([{"high": 100.02, "low": 99.7, "close": 99.8} for _ in range(10)])

    result = compute_micro_momentum_after_entry(frame, 100)

    assert result["mae_5s_pct"] <= -0.25
    assert result["micro_failure"] is True


def test_micro_momentum_after_entry_detects_success():
    frame = pd.DataFrame([{"high": 100.25, "low": 99.98, "close": 100.2} for _ in range(10)])

    result = compute_micro_momentum_after_entry(frame, 100)

    assert result["micro_success"] is True
    assert result["first_5s_reaction"] == "FAVORABLE"
