import pandas as pd

from features.micro_signal_features import compute_micro_signal_features


def test_micro_signal_features_price_change_and_buy_ratio():
    times = pd.date_range("2026-05-01 09:00:00", periods=11, freq="s")
    seconds = [{"time": t, "close": 100 + i * 0.02, "volume": 1.0} for i, t in enumerate(times)]
    ticks = [{"time": times[-1] - pd.Timedelta(seconds=i), "ask_bid": "BID"} for i in range(4)]
    ticks.append({"time": times[-1], "ask_bid": "ASK"})

    result = compute_micro_signal_features(seconds, ticks, as_of_time=times[-1])

    assert result["price_change_5s_pct"] > 0
    assert result["buy_trade_ratio_5s"] >= 0.8
    assert result["micro_state"] in {"ACCELERATING", "STABLE"}
