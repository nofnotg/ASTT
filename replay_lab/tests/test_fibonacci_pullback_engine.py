import pandas as pd

from daddy_strategy.fibonacci_pullback_engine import detect_fibonacci_pullback


def test_fibonacci_pullback_engine_returns_fib_levels():
    frame = pd.DataFrame({"high": [100 + i for i in range(60)], "low": [90 for _ in range(60)], "close": [125 for _ in range(60)]})
    result = detect_fibonacci_pullback(frame)
    assert "fib_50" in result
